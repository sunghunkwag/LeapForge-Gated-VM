"""Scaffold subprocess bootstrap (trusted code that hosts UNtrusted code).

Launched by broker.py as:  unshare -n python3 -m runner.scaffold_runner
with two inherited pipe fds (3 = parent->child, 4 = child->parent).

Responsibilities:
  1. read the init frame (task + budget caps + the candidate scaffold sources)
     from the parent over fd 3;
  2. build a RESTRICTED namespace: safe builtins only, a guarded __import__
     that admits nothing but the stdlib allowlist, no open/eval/exec/etc.;
  3. exec the scaffold sources (in manifest order) into that one shared
     namespace -- so the scaffold's files share globals and never need import
     statements between themselves;
  4. construct the client-side Ctx and call solve(ctx, task);
  5. report completion (or a controlled error) back to the parent.

The scaffold thus runs with NO network (unshare -n), NO filesystem primitive
(open/os absent from its builtins), and reaches the world only through ctx.
"""

import json
import os
import traceback

from .ctx_client import Ctx, Halt
from .restricted import safe_builtins


def _read_frame(rf):
    line = rf.readline()
    if not line:
        raise SystemExit("no init frame from broker")
    return json.loads(line)


def main():
    # fd 3: parent -> child ; fd 4: child -> parent
    resp_fd = int(os.environ.get("SICA_RESP_FD", "3"))
    req_fd = int(os.environ.get("SICA_REQ_FD", "4"))
    rf = os.fdopen(os.dup(resp_fd), "r", encoding="utf-8")
    wf = os.fdopen(os.dup(req_fd), "w", encoding="utf-8")

    init = _read_frame(rf)
    task = init["task"]
    caps = init["caps"]
    sources = init["sources"]          # [[name, src], ...] in exec order

    # The Ctx owns the real fds; hand it fresh dups so its buffering is its own.
    ctx = Ctx(os.dup(req_fd), os.dup(resp_fd), task, caps)

    ns = {"__builtins__": safe_builtins(), "__name__": "scaffold"}
    try:
        for name, src in sources:
            code = compile(src, "scaffold/%s" % name, "exec")
            exec(code, ns)  # noqa: S102 -- restricted namespace, audited source
    except Exception:  # noqa
        _report(wf, {"op": "result", "status": "load_error",
                     "error": traceback.format_exc()[-1500:]})
        return

    solve = ns.get("solve")
    if not callable(solve):
        _report(wf, {"op": "result", "status": "no_solve",
                     "error": "scaffold defines no solve(ctx, task)"})
        return

    try:
        solve(ctx, ctx.task)
        _report(wf, {"op": "result", "status": "done"})
    except Halt as h:
        _report(wf, {"op": "result", "status": "halt", "error": str(h)})
    except Exception:  # noqa -- scaffold bug: report, do not crash the broker
        _report(wf, {"op": "result", "status": "scaffold_error",
                     "error": traceback.format_exc()[-1500:]})


def _report(wf, msg):
    try:
        wf.write(json.dumps(msg, separators=(",", ":")) + "\n")
        wf.flush()
    except Exception:  # noqa
        pass


if __name__ == "__main__":
    main()
