"""One task attempt: materialise a workdir, run the scaffold under the broker,
grade the result with hidden tests. Returns a compact, loggable record.

The workdir receives ONLY the pristine buggy repo/ (source + public tests).
gold/, hidden/, and meta.json are never copied in, so the agent cannot read
them by any means (G-isolate). Grading happens afterward in grade.py.
"""

import os
import shutil
import tempfile

from . import grade
from .broker import Broker
from .meters import Meter


def attempt_task(task, scaffold_sources, model_client, caps, logger=None,
                 keep_workdir=False):
    log = logger or (lambda *a: None)
    tmp = tempfile.mkdtemp(prefix="sica-task-")
    workdir = os.path.join(tmp, "work")
    try:
        shutil.copytree(task.repo_dir, workdir,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        meter = Meter(caps)
        broker = Broker(workdir, task.public_dict(), meter, model_client,
                        task.public_test_paths, logger=log)
        bres = broker.run(scaffold_sources)

        # Non-editable, non-test files present in the repo -- factual context
        # for the failure digest (what the agent COULD have read but a weak
        # scaffold may not have). Not a hint at the fix; just the file list.
        tests = set(task.public_test_paths)
        editable = set(task.editable_files)
        context_files = [f for f in task.repo_files()
                         if f not in editable and f not in tests
                         and not os.path.basename(f).startswith("test_")]
        record = {
            "task": task.id, "difficulty": task.difficulty,
            "issue": task.issue,
            "editable_files": list(task.editable_files),
            "context_files": context_files,
            "status": bres.status, "error": bres.error,
            "violation": bres.violation,
            "meter": meter.snapshot(),
            "notes": bres.notes[-12:],
            "child_stdout": bres.child_stdout[-1200:],
            "solved": False,
        }
        if bres.violation:
            # scope-escape / grading-asset access: do NOT grade; flag the run.
            record["halt_reason"] = "violation"
            return record

        g = grade.grade_solution(task, workdir, clock=meter.clock)
        record["solved"] = g["solved"]
        record["grade"] = {"f2p_ok": g["f2p"]["ok"], "p2p_ok": g["p2p"]["ok"],
                           "f2p_rc": g["f2p"].get("rc"),
                           "p2p_rc": g["p2p"].get("rc")}
        return record
    finally:
        if not keep_workdir:
            shutil.rmtree(tmp, ignore_errors=True)


def failure_digest(records, limit=6):
    """Build a compact, heldout-free failure summary for the proposer.
    Includes only TRAIN attempts (caller guarantees this)."""
    fails = [r for r in records if not r.get("solved")]
    out = []
    for r in fails[:limit]:
        out.append({
            "task": r["task"],
            "difficulty": r.get("difficulty"),
            # what the failing task actually ASKED (directive 1.1: the proposer
            # reads its own failing transcripts) and what files were present --
            # so a recurring "answer defined in another file the agent never
            # read" mode is visible in the transcripts, not hidden.
            "issue": (r.get("issue") or "")[:300],
            "editable_files": r.get("editable_files", []),
            "other_files_present": r.get("context_files", []),
            "status": r["status"],
            "error": (r.get("error") or "")[:300],
            "meter": {k: r["meter"].get(k) for k in
                      ("model_calls", "tool_calls", "steps", "model_tokens")},
            "notes": r.get("notes", [])[-4:],
            "trace_tail": (r.get("child_stdout") or "")[-400:],
        })
    return out
