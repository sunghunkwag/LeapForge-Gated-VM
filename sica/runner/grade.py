"""Sealed grading (the operational half of G-isolate).

The agent never sees the hidden tests. Grading happens here, in the trusted
parent, AFTER the agent finishes:

  1. build an eval copy = pristine buggy repo
       + overlay ONLY the task's editable files, taken from `source_root`
         (the agent's workdir when grading a solution; gold/ when validating
         the task; nothing for the buggy baseline),
       + overlay the hidden grading tests.
     Because only the declared editable files are carried across, a scaffold
     cannot pass grading by side-effect (a stray conftest.py, a monkeypatch,
     an edited public test) -- none of that reaches the eval copy.
  2. run fail_to_pass and pass_to_pass under the network-isolated sandbox.

solved  <=>  every fail_to_pass passes AND every pass_to_pass passes.

The same machinery validates a task is honest: on the buggy baseline the
fail_to_pass tests must FAIL and pass_to_pass must PASS; on gold both must
PASS. A task that does not exhibit that fail->pass transition is rejected.
"""

import os
import shutil
import sys
import tempfile

from . import sandbox


def _copytree(src, dst):
    shutil.copytree(src, dst, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def build_eval_copy(task, dest, source_root=None):
    """dest must not exist. source_root supplies the editable files (or None to
    keep the buggy originals). Hidden grading tests are always overlaid."""
    _copytree(task.repo_dir, dest)
    if source_root is not None:
        for rel in task.editable_files:
            src = os.path.join(source_root, rel)
            dstp = os.path.join(dest, rel)
            if os.path.isfile(src):
                d = os.path.dirname(dstp)
                if d and not os.path.isdir(d):
                    os.makedirs(d)
                shutil.copy2(src, dstp)
            # if the agent removed an editable file, keep the buggy original
    if os.path.isdir(task.hidden_dir):
        _copytree(task.hidden_dir, dest)
    return dest


def _run_group(dest, targets, timeout, clock=None):
    """Run a set of pytest targets. Returns {ok, collected, rc, passed,
    failed, errors}. ok == all passed and something ran."""
    if not targets:
        return {"ok": True, "collected": True, "rc": 0, "passed": 0,
                "failed": 0, "errors": 0, "empty": True}
    argv = [sys.executable, "-m", "pytest", "-q", "--no-header",
            "-p", "no:cacheprovider"] + list(targets)
    r = sandbox.run_test_command(argv, dest, timeout=timeout, clock=clock)
    from .broker import _parse_pytest
    passed, failed, errors = _parse_pytest(r.stdout, r.stderr)
    collected = r.code != 5              # rc 5 == no tests collected
    ok = (r.code == 0) and collected and failed == 0 and errors == 0
    return {"ok": ok, "collected": collected, "rc": r.code, "passed": passed,
            "failed": failed, "errors": errors,
            "stdout": r.stdout[-1500:], "empty": False}


def grade_solution(task, agent_workdir, timeout=90, clock=None):
    """Grade the agent's workdir. Returns {solved, f2p, p2p}."""
    tmp = tempfile.mkdtemp(prefix="sica-grade-")
    dest = os.path.join(tmp, "eval")
    try:
        build_eval_copy(task, dest, source_root=agent_workdir)
        f2p = _run_group(dest, task.fail_to_pass, timeout, clock)
        p2p = _run_group(dest, task.pass_to_pass, timeout, clock)
        solved = bool(f2p["ok"] and p2p["ok"])
        return {"solved": solved, "f2p": f2p, "p2p": p2p}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def validate_task(task, timeout=90, clock=None):
    """Confirm the task is honest and its signal is real. Returns a report;
    report['valid'] is True iff the fail->pass transition holds."""
    tmp = tempfile.mkdtemp(prefix="sica-val-")
    reasons = []
    try:
        # buggy baseline: fail_to_pass must FAIL, pass_to_pass must PASS
        buggy = os.path.join(tmp, "buggy")
        build_eval_copy(task, buggy, source_root=None)
        b_f2p = _run_group(buggy, task.fail_to_pass, timeout, clock)
        b_p2p = _run_group(buggy, task.pass_to_pass, timeout, clock)
        if not b_f2p["collected"]:
            reasons.append("fail_to_pass collected nothing on buggy")
        if b_f2p["ok"]:
            reasons.append("fail_to_pass already PASSES on buggy (no bug)")
        if not b_p2p["ok"]:
            reasons.append("pass_to_pass does not pass on buggy baseline")

        # gold: fail_to_pass must PASS, pass_to_pass must PASS
        gold = os.path.join(tmp, "gold")
        build_eval_copy(task, gold, source_root=task.gold_dir)
        g_f2p = _run_group(gold, task.fail_to_pass, timeout, clock)
        g_p2p = _run_group(gold, task.pass_to_pass, timeout, clock)
        if not g_f2p["ok"]:
            reasons.append("fail_to_pass does NOT pass on gold")
        if not g_p2p["ok"]:
            reasons.append("pass_to_pass does not pass on gold")

        valid = not reasons
        return {"valid": valid, "reasons": reasons,
                "buggy_f2p": b_f2p, "buggy_p2p": b_p2p,
                "gold_f2p": g_f2p, "gold_p2p": g_p2p}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
