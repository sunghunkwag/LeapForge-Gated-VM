"""The `ctx` capability object, as seen by the scaffold (client side).

This runs INSIDE the scaffold subprocess. It holds no real capability -- it
marshals every request over a pipe to the trusted parent (broker.py), which is
the only party that can call the model, touch the filesystem, or run a test.
The subprocess has no network namespace, and the scaffold's builtins lack
open/import-of-anything-dangerous, so `ctx` is the scaffold's ONLY route to the
outside world. That is what makes G-isolate and G-sandbox structural.

The scaffold's whole tool surface is the methods here. Richer tools (a symbol
index, a focused test runner, a diff minimiser) are meant to be *composed* from
these primitives inside the scaffold -- that is the tool-growth mechanism.
"""

import json
import os


class Halt(Exception):
    """Raised when the parent refuses a call fatally (budget breach, isolation
    violation). Propagates out of solve(); the task ends, scored unsolved."""


class _Task(object):
    def __init__(self, d):
        self._d = d

    @property
    def name(self):
        return self._d.get("name")

    @property
    def issue(self):
        """Natural-language problem statement (the 'issue text')."""
        return self._d.get("issue", "")

    @property
    def editable_files(self):
        """The files the agent may edit; grading only reads these back."""
        return list(self._d.get("editable_files", []))

    @property
    def files(self):
        """All source files visible in the workdir (relative paths)."""
        return list(self._d.get("files", []))

    @property
    def test_command(self):
        """The public test command, as a hint (list of argv tokens)."""
        return list(self._d.get("test_command", []))

    def get(self, k, default=None):
        return self._d.get(k, default)


class Ctx(object):
    def __init__(self, req_fd, resp_fd, task_dict, caps):
        self._wf = os.fdopen(req_fd, "w", encoding="utf-8")
        self._rf = os.fdopen(resp_fd, "r", encoding="utf-8")
        self.task = _Task(task_dict)
        self.caps = dict(caps)  # advisory copy of the budget caps
        self._notes = []

    # ------------------------------------------------------------- transport
    def _rpc(self, op, **kw):
        msg = dict(kw)
        msg["op"] = op
        self._wf.write(json.dumps(msg, separators=(",", ":")) + "\n")
        self._wf.flush()
        line = self._rf.readline()
        if not line:
            raise Halt("broker closed the channel")
        resp = json.loads(line)
        if not resp.get("ok"):
            if resp.get("fatal"):
                raise Halt(resp.get("error", "fatal"))
            raise RuntimeError(resp.get("error", "call failed"))
        return resp.get("result")

    # ---------------------------------------------------------------- model
    def model(self, prompt, system=None, max_tokens=2048):
        """One metered model completion. Returns the text."""
        return self._rpc("model", prompt=prompt, system=system or "",
                         max_tokens=max_tokens)

    # ------------------------------------------------------------ filesystem
    def read(self, path):
        """Read a file inside the task workdir. Returns str, or None if absent."""
        return self._rpc("read", path=path)

    def write(self, path, content):
        """Write a file inside the task workdir."""
        self._rpc("write", path=path, content=content)
        return True

    def ls(self, path="."):
        """List entries under a workdir-relative directory."""
        return self._rpc("ls", path=path)

    def grep(self, pattern, path=".", max_hits=200):
        """Regex search across workdir files. Returns [{path,line,text}]."""
        return self._rpc("grep", pattern=pattern, path=path, max_hits=max_hits)

    # ------------------------------------------------------------------ tests
    def run_tests(self, paths=None, timeout=60):
        """Run the PUBLIC tests (never the hidden grading tests) in a
        no-network sandbox. Returns {code, passed, failed, stdout, stderr}."""
        return self._rpc("run_tests", paths=paths or None, timeout=timeout)

    # ------------------------------------------------------------------- misc
    def log(self, msg):
        self._notes.append(str(msg))
        try:
            self._rpc("log", msg=str(msg)[:500])
        except RuntimeError:
            pass

    def step(self):
        """Advance the plan->act->verify step counter (metered)."""
        return self._rpc("step")
