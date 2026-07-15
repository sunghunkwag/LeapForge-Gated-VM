#!/usr/bin/env python3
"""Headroom probe: score GEN0 and the current adopted scaffold on a benchmark's
held-out split, to check a new axis actually has headroom before running the
engine on it. Usage: python3 tools/headroom.py <tasks_subdir> [seed]"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runner import config, sandbox, scaffold_io           # noqa: E402
from runner.bench.localsuite import LocalSuite             # noqa: E402
from runner.evaluate import evaluate_scaffold              # noqa: E402
from runner.model import ModelClient                       # noqa: E402

GEN0_DIR = os.path.join(config.ARCHIVE_DIR, "a4d1fe5ee554_afa858",
                        "gen00_beba47153812e099")


def main(argv):
    subdir = argv[1] if len(argv) > 1 else "tasks_axis2"
    seed = argv[2] if len(argv) > 2 else "s1"
    sandbox.require_isolation()
    cfg = config.make_config("smoke", "claude_cli", seed, {"K": 4})
    caps = cfg["task_budget"]
    gen0 = scaffold_io.load_scaffold(GEN0_DIR)
    adopted = scaffold_io.load_scaffold(config.SCAFFOLD_DIR)
    bench = LocalSuite(tasks_root=os.path.join(config.RUNNER_DIR, "bench", subdir))
    tr, he = bench.split(seed, cfg["n_train"], cfg["n_heldout"])
    mc = ModelClient(backend="claude_cli", model=cfg["model_pinned"])
    print("%s held-out (%s): %s" % (subdir, seed, ", ".join(t.id for t in he)))
    g0 = evaluate_scaffold(gen0, he, mc, caps, concurrency=8,
                           logger=lambda *a: None, label="gen0")
    ad = evaluate_scaffold(adopted, he, mc, caps, concurrency=8,
                           logger=lambda *a: None, label="adopted")
    adok = {r["task"] for r in ad["records"] if r and r.get("solved")}
    g0ok = {r["task"] for r in g0["records"] if r and r.get("solved")}
    out = {
        "subdir": subdir, "seed": seed,
        "held_ids": [t.id for t in he],
        "gen0_solved": g0["solved"], "adopted_solved": ad["solved"], "n": he.__len__(),
        "adopted_solved_ids": sorted(adok),
        "adopted_failed_ids": sorted(t.id for t in he if t.id not in adok),
        "gen0_solved_ids": sorted(g0ok),
        "cost": mc.session_totals()["cost_usd"],
    }
    print("GEN0    %s held-out: %d/%d" % (subdir, g0["solved"], g0["n"]))
    print("ADOPTED %s held-out: %d/%d  <- HEADROOM (want ~4-7/10)"
          % (subdir, ad["solved"], ad["n"]))
    print("adopted FAILED:", out["adopted_failed_ids"])
    print("cost: $%.4f" % out["cost"])
    dest = os.path.join(config.RUNS_DIR, "headroom_%s_%s.json" % (subdir, seed))
    if not os.path.isdir(config.RUNS_DIR):
        os.makedirs(config.RUNS_DIR)
    json.dump(out, open(dest, "w"), indent=2)
    print("-> %s" % dest)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
