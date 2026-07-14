#!/usr/bin/env python3
"""Replication harness: is the adopted scaffold's held-out gain a fluke?

Paired A/B measurement of TWO FIXED scaffolds -- the GEN0 seed and the
T8-approved adopted scaffold `enable-grep-localize-function` -- on the held-out
slices of SEVERAL fresh seeds. Each seed produces a DIFFERENT repository-disjoint
split of tasks_hard, so a per-seed win on held-out the scaffold never trained or
was tuned on is genuine replication, not one-split luck.

No proposer, no gate, no adoption: this is purely the final measurement step
(scoring a fixed scaffold on held-out), run through the same evaluate_scaffold /
broker / unshare path the engine uses, with the same per-task caps. G-heldout is
not at risk -- nothing here feeds back into any proposal.

Usage: python3 tools/replicate.py [seed ...]   (default: s2 s3 s4)
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runner import config, sandbox, scaffold_io          # noqa: E402
from runner.bench.localsuite import LocalSuite            # noqa: E402
from runner.evaluate import evaluate_scaffold             # noqa: E402
from runner.model import ModelClient                      # noqa: E402

TASKS_HARD = os.path.join(config.RUNNER_DIR, "bench", "tasks_hard")
GEN0_DIR = os.path.join(
    config.ARCHIVE_DIR, "a4d1fe5ee554_afa858", "gen00_beba47153812e099")
ADOPTED_DIR = config.SCAFFOLD_DIR   # current committed incumbent


def main(argv):
    seeds = argv[1:] or ["s2", "s3", "s4"]
    sandbox.require_isolation()
    cfg = config.make_config("smoke", "claude_cli", "rep", {"K": 4})
    caps = cfg["task_budget"]
    n_heldout = cfg["n_heldout"]
    n_train = cfg["n_train"]

    gen0 = scaffold_io.load_scaffold(GEN0_DIR)
    adopted = scaffold_io.load_scaffold(ADOPTED_DIR)
    scaffold_io.audit_scaffold(gen0)
    scaffold_io.audit_scaffold(adopted)
    print("GEN0 sha=%s   adopted sha=%s"
          % (scaffold_io.scaffold_sha(gen0), scaffold_io.scaffold_sha(adopted)))

    model = ModelClient(backend="claude_cli", model=cfg["model_pinned"])
    bench = LocalSuite(tasks_root=TASKS_HARD)

    rows = []
    for seed in seeds:
        train, heldout = bench.split(seed, n_train, n_heldout)
        held_ids = [t.id for t in heldout]
        print("\n=== seed %s : held-out (%d, repo-disjoint from train) ===\n  %s"
              % (seed, len(heldout), ", ".join(held_ids)))

        g0 = evaluate_scaffold(gen0, heldout, model, caps,
                               concurrency=cfg["concurrency"],
                               logger=lambda *a: None, label="gen0")
        ad = evaluate_scaffold(adopted, heldout, model, caps,
                               concurrency=cfg["concurrency"],
                               logger=lambda *a: None, label="adopted")
        delta = ad["solved"] - g0["solved"]
        g0_solved = {r["task"] for r in g0["records"] if r and r.get("solved")}
        ad_solved = {r["task"] for r in ad["records"] if r and r.get("solved")}
        newly = sorted(ad_solved - g0_solved)
        lost = sorted(g0_solved - ad_solved)
        print("  GEN0    held-out %d/%d" % (g0["solved"], g0["n"]))
        print("  ADOPTED held-out %d/%d   (delta %+d)"
              % (ad["solved"], ad["n"], delta))
        print("  newly solved by adopted: %s" % (newly or "-"))
        print("  regressed (GEN0 solved, adopted lost): %s" % (lost or "-"))
        rows.append({
            "seed": seed, "held_ids": held_ids,
            "gen0_solved": g0["solved"], "adopted_solved": ad["solved"],
            "n": g0["n"], "delta": delta,
            "newly_solved": newly, "regressed": lost,
            "gen0_score": g0["score"], "adopted_score": ad["score"],
        })

    # --- summary ---
    print("\n" + "=" * 60)
    print("REPLICATION SUMMARY (fixed scaffolds, fresh held-out splits)")
    print("=" * 60)
    print("  %-6s %-10s %-12s %s" % ("seed", "GEN0", "ADOPTED", "delta"))
    tot_g0 = tot_ad = tot_n = 0
    wins = 0
    for r in rows:
        print("  %-6s %d/%-8d %d/%-10d %+d"
              % (r["seed"], r["gen0_solved"], r["n"], r["adopted_solved"],
                 r["n"], r["delta"]))
        tot_g0 += r["gen0_solved"]
        tot_ad += r["adopted_solved"]
        tot_n += r["n"]
        wins += 1 if r["delta"] > 0 else 0
    print("  %-6s %d/%-8d %d/%-10d %+d"
          % ("ALL", tot_g0, tot_n, tot_ad, tot_n, tot_ad - tot_g0))
    print("\n  pooled GEN0    held-out: %d/%d = %.0f%%"
          % (tot_g0, tot_n, 100.0 * tot_g0 / tot_n))
    print("  pooled ADOPTED held-out: %d/%d = %.0f%%"
          % (tot_ad, tot_n, 100.0 * tot_ad / tot_n))
    print("  seeds where adopted > GEN0: %d/%d" % (wins, len(rows)))
    print("  session cost: $%.4f" % model.session_totals()["cost_usd"])

    out = {"seeds": seeds, "rows": rows,
           "pooled": {"gen0": tot_g0, "adopted": tot_ad, "n": tot_n,
                      "wins": wins, "n_seeds": len(rows)},
           "session_totals": model.session_totals(),
           "gen0_sha": scaffold_io.scaffold_sha(gen0),
           "adopted_sha": scaffold_io.scaffold_sha(adopted),
           "benchmark_pin": bench.pin()}
    dest = os.path.join(config.RUNS_DIR, "replication.json")
    if not os.path.isdir(config.RUNS_DIR):
        os.makedirs(config.RUNS_DIR)
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print("  -> %s" % dest)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
