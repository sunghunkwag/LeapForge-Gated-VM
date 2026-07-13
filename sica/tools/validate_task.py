#!/usr/bin/env python3
"""Standalone task validator. Confirms a localsuite task's fail->pass signal is
real: on the BUGGY snapshot the hidden fail_to_pass tests FAIL and pass_to_pass
PASS; on GOLD both PASS.

Usage:  python3 tools/validate_task.py <path/to/repo/task_dir>
Exit 0 = valid, 1 = invalid (reasons printed).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runner.bench.base import Task, load_meta   # noqa: E402
from runner import grade, sandbox               # noqa: E402


def main(argv):
    if len(argv) != 2:
        print("usage: validate_task.py <task_dir>")
        return 2
    task_dir = argv[1]
    if not os.path.isfile(os.path.join(task_dir, "meta.json")):
        print("INVALID: no meta.json in %s" % task_dir)
        return 1
    ok, why = sandbox.probe_isolation()
    if not ok:
        print("WARNING: network isolation unavailable (%s); validating "
              "without it" % why)
    task = Task(task_dir, load_meta(task_dir))
    rep = grade.validate_task(task)
    if rep["valid"]:
        print("VALID   %s  (difficulty=%s)" % (task.id, task.difficulty))
        return 0
    print("INVALID %s" % task.id)
    for r in rep["reasons"]:
        print("  - %s" % r)
    print("  buggy_f2p rc=%s  gold_f2p rc=%s"
          % (rep["buggy_f2p"].get("rc"), rep["gold_f2p"].get("rc")))
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
