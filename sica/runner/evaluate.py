"""Evaluate a scaffold over a task slice (parallelised).

Each task is an independent attempt_task() -- its own workdir, subprocess,
meter, and sealed grade -- so they run concurrently on a thread pool (the work
is IO/subprocess-bound). The SAME model client and caps are used for every
scaffold, which is what lets the gate compare candidates against the incumbent
on identical tasks/seeds/budget (directive section 2/3).
"""

from concurrent.futures import ThreadPoolExecutor, as_completed

from . import harness, scaffold_io
from .meters import sum_snapshots


def evaluate_scaffold(scaffold, tasks, model_client, caps, concurrency=4,
                      logger=None, label=""):
    log = logger or (lambda *a: None)
    sources = scaffold_io.scaffold_sources(scaffold)
    records = [None] * len(tasks)

    def work(i):
        rec = harness.attempt_task(tasks[i], sources, model_client, caps,
                                   logger=None)
        return i, rec

    if concurrency <= 1 or len(tasks) <= 1:
        for i in range(len(tasks)):
            _i, rec = work(i)
            records[i] = rec
            log("    [%s] %-22s %s" % (label, tasks[i].id,
                "solved" if rec.get("solved") else rec.get("status")))
    else:
        with ThreadPoolExecutor(max_workers=concurrency) as ex:
            futs = [ex.submit(work, i) for i in range(len(tasks))]
            for fut in as_completed(futs):
                i, rec = fut.result()
                records[i] = rec
                log("    [%s] %-22s %s" % (label, tasks[i].id,
                    "solved" if rec.get("solved") else rec.get("status")))

    solved = sum(1 for r in records if r and r.get("solved"))
    violation = None
    for r in records:
        if r and r.get("violation"):
            violation = r["violation"]
            break
    meter_total = sum_snapshots([r["meter"] for r in records if r])
    n = len(tasks)
    return {
        "records": records,
        "solved": solved,
        "n": n,
        "score": (solved / float(n)) if n else 0.0,
        "meter": meter_total,
        "violation": violation,
        "sha": scaffold_io.scaffold_sha(scaffold),
    }
