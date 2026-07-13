"""Broker: the trusted parent that serves the scaffold subprocess.

It launches the scaffold under `unshare -n`, hands it a task workdir and the
candidate scaffold sources over a pipe, then answers its ctx requests. Every
answer is a chokepoint where the four guardrails are enforced:

  G-isolate : file ops are realpath-confined to the workdir; the workdir never
              contains hidden grading tests or gold patches, so they are
              unreachable. Any path that resolves outside the workdir is a
              scope-escape -> fatal + run-halt flag (directive section 5).
  G-heldout : the broker has no knowledge of heldout results; it only serves
              solving. (Heldout scoring is a separate, later step.)
  G-sandbox : the child has no network namespace; test commands run through the
              sandbox (allowlisted executables, stripped env, no network).
  G-budget  : the Meter is checked BEFORE every model/tool/step, so a breach
              prevents the spend and ends the task.
"""

import json
import os
import re
import select
import signal
import subprocess
import sys
import tempfile

from . import sandbox
from .meters import BudgetError

_PYTEST_SUMMARY = re.compile(
    r"(?:(\d+) passed)?(?:, )?(?:(\d+) failed)?(?:, )?(?:(\d+) error)?")


class BrokerResult(object):
    def __init__(self):
        self.status = "unknown"
        self.error = None
        self.violation = None       # set on a scope-escape / isolation breach
        self.notes = []
        self.child_stdout = ""


def _safe_join(workdir, rel):
    """Confine `rel` to `workdir`; raise on escape (grading-asset attempt)."""
    if not isinstance(rel, str):
        raise PermissionError("path must be a string")
    full = os.path.realpath(os.path.join(workdir, rel))
    wd = os.path.realpath(workdir)
    if full != wd and not full.startswith(wd + os.sep):
        raise PermissionError("path escapes workdir: %r" % rel)
    return full


def _parse_pytest(stdout, stderr):
    passed = failed = errors = 0
    for line in (stdout + "\n" + stderr).splitlines()[::-1]:
        if "passed" in line or "failed" in line or "error" in line:
            m = _PYTEST_SUMMARY.search(line)
            if m and any(m.groups()):
                passed = int(m.group(1) or 0)
                failed = int(m.group(2) or 0)
                errors = int(m.group(3) or 0)
                break
    return passed, failed, errors


class Broker(object):
    def __init__(self, workdir, task_public, meter, model_client,
                 public_test_paths, logger=None):
        self.workdir = os.path.realpath(workdir)
        self.task_public = task_public
        self.meter = meter
        self.model = model_client
        self.public_test_paths = public_test_paths
        self.log = logger or (lambda *a: None)

    # ------------------------------------------------------------------ run
    def run(self, scaffold_sources):
        """scaffold_sources: [[name, src], ...] in exec order. Blocks until the
        scaffold reports a result or is killed on wall-timeout."""
        res = BrokerResult()
        parent_r, child_w = os.pipe()     # child -> parent (requests)
        child_r, parent_w = os.pipe()     # parent -> child (responses/init)

        env = dict(os.environ)
        env["SICA_RESP_FD"] = str(child_r)
        env["SICA_REQ_FD"] = str(child_w)
        env["PYTHONPATH"] = (os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))) + os.pathsep + env.get("PYTHONPATH", ""))
        argv = sandbox.wrap_no_network(
            [sys.executable, "-m", "runner.scaffold_runner"])
        # child stdout/stderr -> temp file (drained after reap) so scaffold
        # prints can never fill a pipe and deadlock the protocol channel.
        out_f = tempfile.TemporaryFile(mode="w+", encoding="utf-8",
                                       errors="replace")
        # neutral cwd so no stray relative open in trusted bootstrap resolves
        # anywhere interesting; the scaffold itself has no open at all.
        proc = subprocess.Popen(
            argv, env=env, cwd="/tmp",
            pass_fds=(child_r, child_w),
            stdout=out_f, stderr=subprocess.STDOUT,
            preexec_fn=os.setsid if hasattr(os, "setsid") else None,
        )
        os.close(child_r)
        os.close(child_w)
        wf = os.fdopen(parent_w, "w", encoding="utf-8")
        rf = os.fdopen(parent_r, "r", encoding="utf-8")

        # init frame
        init = {"task": self.task_public, "caps": self.meter.caps,
                "sources": scaffold_sources}
        try:
            wf.write(json.dumps(init, separators=(",", ":")) + "\n")
            wf.flush()
            self._serve(rf, wf, proc, res)
        finally:
            try:
                wf.close()
            except Exception:  # noqa
                pass
            try:
                rf.close()
            except Exception:  # noqa
                pass
            self._reap(proc)
            try:
                out_f.seek(0)
                res.child_stdout = out_f.read()[-4000:]
                out_f.close()
            except Exception:  # noqa
                pass
        return res

    # ---------------------------------------------------------------- serve
    def _serve(self, rf, wf, proc, res):
        fd = rf.fileno()
        while True:
            timeout = max(1.0, self.meter.caps["wall_seconds"]
                          - (self.meter.clock() - self.meter.t0))
            ready, _, _ = select.select([fd], [], [], timeout)
            if not ready:
                # wall-clock watchdog: child produced no request in time
                res.status = "timeout"
                res.error = "wall-clock watchdog fired"
                return
            line = rf.readline()
            if not line:
                res.status = res.status if res.status != "unknown" else "eof"
                return
            try:
                req = json.loads(line)
            except ValueError:
                self._respond(wf, ok=False, error="bad json", fatal=True)
                res.status = "protocol_error"
                return
            op = req.get("op")
            if op == "result":
                res.status = req.get("status", "done")
                res.error = req.get("error")
                return
            done = self._handle(op, req, wf, res)
            if done:
                return

    def _handle(self, op, req, wf, res):
        try:
            if op == "log":
                res.notes.append(str(req.get("msg", ""))[:500])
                self._respond(wf, ok=True, result=None)
            elif op == "step":
                self.meter.check_step()
                self.meter.record_step()
                self._respond(wf, ok=True, result=self.meter.steps)
            elif op == "model":
                self.meter.check_model()
                text, usage = self.model.complete(
                    req.get("system", ""), req.get("prompt", ""),
                    max_tokens=int(req.get("max_tokens", 2048)))
                self.meter.record_model(usage["input_tokens"],
                                        usage["output_tokens"],
                                        usage["cost_usd"])
                self._respond(wf, ok=True, result=text)
            elif op == "read":
                self._respond(wf, ok=True, result=self._read(req["path"]))
            elif op == "write":
                self._write(req["path"], req.get("content", ""))
                self._respond(wf, ok=True, result=None)
            elif op == "ls":
                self._respond(wf, ok=True, result=self._ls(req.get("path", ".")))
            elif op == "grep":
                self._respond(wf, ok=True, result=self._grep(
                    req["pattern"], req.get("path", "."),
                    int(req.get("max_hits", 200))))
            elif op == "run_tests":
                self.meter.check_tool()
                out = self._run_tests(req.get("paths"),
                                      int(req.get("timeout", 60)))
                self.meter.record_tool()
                self._respond(wf, ok=True, result=out)
            else:
                self._respond(wf, ok=False, error="unknown op %r" % op,
                              fatal=False)
        except BudgetError as e:
            self._respond(wf, ok=False, error=str(e), fatal=True)
            res.status = "budget"
            res.error = str(e)
            return True
        except PermissionError as e:
            # scope-escape / grading-asset access attempt -> halt the run
            res.violation = str(e)
            res.status = "violation"
            res.error = str(e)
            self._respond(wf, ok=False, error=str(e), fatal=True)
            return True
        except Exception as e:  # noqa -- a broker-side op failure is non-fatal
            self._respond(wf, ok=False, error="%s: %s" % (type(e).__name__, e),
                          fatal=False)
        return False

    # ------------------------------------------------------- capability impls
    def _read(self, rel):
        full = _safe_join(self.workdir, rel)
        if not os.path.isfile(full):
            return None
        with open(full, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def _write(self, rel, content):
        full = _safe_join(self.workdir, rel)
        d = os.path.dirname(full)
        if d and not os.path.isdir(d):
            os.makedirs(d)
        with open(full, "w", encoding="utf-8") as f:
            f.write(content if isinstance(content, str) else str(content))

    def _ls(self, rel):
        full = _safe_join(self.workdir, rel)
        if os.path.isfile(full):
            return [os.path.basename(full)]
        if not os.path.isdir(full):
            return []
        out = []
        for name in sorted(os.listdir(full)):
            p = os.path.join(full, name)
            out.append(name + ("/" if os.path.isdir(p) else ""))
        return out

    def _grep(self, pattern, rel, max_hits):
        try:
            rx = re.compile(pattern)
        except re.error as e:
            raise ValueError("bad regex: %s" % e)
        base = _safe_join(self.workdir, rel)
        hits = []
        roots = [base] if os.path.isdir(base) else [os.path.dirname(base)]
        for root in roots:
            for dirpath, dirs, files in os.walk(root):
                dirs[:] = [d for d in dirs if not d.startswith(".")
                           and d != "__pycache__"]
                for fn in sorted(files):
                    if not fn.endswith((".py", ".txt", ".md", ".cfg", ".ini",
                                        ".toml", ".json")):
                        continue
                    fp = os.path.join(dirpath, fn)
                    try:
                        with open(fp, "r", encoding="utf-8",
                                  errors="replace") as f:
                            for i, ln in enumerate(f, 1):
                                if rx.search(ln):
                                    rp = os.path.relpath(fp, self.workdir)
                                    hits.append({"path": rp, "line": i,
                                                 "text": ln.rstrip()[:300]})
                                    if len(hits) >= max_hits:
                                        return hits
                    except OSError:
                        continue
        return hits

    def _run_tests(self, paths, timeout):
        if paths:
            targets = []
            for p in paths:
                _safe_join(self.workdir, p)  # confinement check
                targets.append(p)
        else:
            targets = list(self.public_test_paths)
        argv = [sys.executable, "-m", "pytest", "-q", "--no-header",
                "-p", "no:cacheprovider"] + targets
        r = sandbox.run_test_command(argv, self.workdir,
                                     timeout=min(timeout, 120),
                                     clock=self.meter.clock)
        passed, failed, errors = _parse_pytest(r.stdout, r.stderr)
        return {"code": r.code, "passed": passed, "failed": failed,
                "errors": errors, "timed_out": r.timed_out,
                "stdout": r.stdout[-3000:], "stderr": r.stderr[-1500:]}

    # ------------------------------------------------------------- transport
    def _respond(self, wf, ok, result=None, error=None, fatal=False):
        msg = {"ok": ok}
        if ok:
            msg["result"] = result
        else:
            msg["error"] = error
            msg["fatal"] = fatal
        wf.write(json.dumps(msg, separators=(",", ":")) + "\n")
        wf.flush()

    def _reap(self, proc):
        if proc.poll() is None:
            try:
                if hasattr(os, "killpg"):
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                else:
                    proc.kill()
            except Exception:  # noqa
                try:
                    proc.kill()
                except Exception:  # noqa
                    pass
        try:
            proc.wait(timeout=10)
        except Exception:  # noqa
            pass
