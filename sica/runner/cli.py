"""SICA command line.

  pin                 verify + print the benchmark pin and isolation status
  validate-bench      confirm every task's fail->pass transition is real
  estimate            print the section-5 approval block (no spend)
  verify              $0 deterministic end-to-end engine run (stub model)
  run                 run the engine on a profile (real model; needs --yes)

Section 5: real runs require ONE approval at session start -- the CLI enforces
this by refusing a real-backend run without --yes and an approved --max-cost.
"""

import argparse
import binascii
import os
import sys

from . import config, grade, scaffold_io
from .bench.localsuite import LocalSuite
from .bench import swebench
from .engine import Engine
from .model import ModelClient
from . import sandbox

_HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES_ROOT = os.path.join(_HERE, "bench", "fixtures")


def _dirs():
    return {"ledger": config.LEDGER_DIR, "memory": config.MEMORY_DIR,
            "archive": config.ARCHIVE_DIR, "runs": config.RUNS_DIR}


_BENCH_DIR = os.path.join(_HERE, "bench")


def _benchmark(cfg, verify=False, subdir=None):
    if verify:
        return LocalSuite(tasks_root=FIXTURES_ROOT)
    if cfg["benchmark"] == "swebench":
        swebench.require_runnable()
        raise SystemExit("swebench execution wiring is host-gated; use "
                         "localsuite for the engine loop (see swebench.py).")
    if subdir and subdir != "tasks":
        return LocalSuite(tasks_root=os.path.join(_BENCH_DIR, subdir))
    return LocalSuite()


def _load_incumbent():
    scaffold = scaffold_io.load_scaffold(config.SCAFFOLD_DIR)
    scaffold_io.audit_scaffold(scaffold)   # GEN0 must pass the audit
    return scaffold


# --------------------------------------------------------------- estimate
_AGENT_CALL_USD = 0.0025
_PROPOSER_CALL_USD = 0.012
_AVG_AGENT_CALLS = 3


def estimate(cfg):
    nt, nh, K, G = (cfg["n_train"], cfg["n_heldout"], cfg["K"],
                    cfg["max_generations"])
    attempts = nh + G * ((1 + K) * nt + nh)
    agent_calls = attempts * _AVG_AGENT_CALLS
    proposer_calls = G * K
    exp = agent_calls * _AGENT_CALL_USD + proposer_calls * _PROPOSER_CALL_USD
    return {
        "task_attempts": attempts,
        "agent_calls_est": agent_calls,
        "proposer_calls": proposer_calls,
        "cost_low_usd": round(exp * 0.5, 2),
        "cost_expected_usd": round(exp, 2),
        "cost_high_usd": round(exp * 2.0, 2),
    }


def print_approval_block(profile, cfg, bench):
    est = estimate(cfg)
    iso_ok, iso_why = sandbox.probe_isolation()
    print("=" * 68)
    print("SICA SESSION APPROVAL BLOCK  (directive section 5)")
    print("=" * 68)
    print("  profile           : %s" % profile)
    print("  base model        : %s  (pinned, no mid-run swap)"
          % cfg["model_pinned"])
    print("  temperature (req) : %s" % cfg["model_temperature"])
    print("  benchmark         : %s" % cfg["benchmark"])
    try:
        pin = bench.pin()
        print("  benchmark pin     : %d tasks / %d repos  sha=%s"
              % (pin["n_tasks"], pin["n_repos"], pin["content_sha256"][:16]))
    except Exception as e:  # noqa
        print("  benchmark pin     : (unavailable: %s)" % e)
    print("  split             : %d train / %d heldout (repo-disjoint)"
          % (cfg["n_train"], cfg["n_heldout"]))
    print("  tournament K      : %d" % cfg["K"])
    print("  max generations   : %d" % cfg["max_generations"])
    print("  per-task caps     : %s" % cfg["task_budget"])
    print("  network isolation : %s (%s)"
          % ("OK" if iso_ok else "UNAVAILABLE", iso_why))
    print("  guardrails        : G-isolate G-heldout G-sandbox G-budget")
    print("  ---- estimated API cost (rough) ----")
    print("  task attempts     : ~%d" % est["task_attempts"])
    print("  model calls       : ~%d agent + %d proposer"
          % (est["agent_calls_est"], est["proposer_calls"]))
    print("  cost estimate     : $%.2f expected  (band $%.2f - $%.2f)"
          % (est["cost_expected_usd"], est["cost_low_usd"],
             est["cost_high_usd"]))
    print("  auto-halts        : budget exhaustion, >%.0fx-baseline gen spend, "
          "%d-gen heldout regression, scope-escape"
          % (cfg["gen_budget_multiple"], cfg["regression_halt"]))
    print("=" * 68)
    return est


# --------------------------------------------------------------- validation
def validate_tasks(tasks, quiet=False):
    bad = []
    for t in tasks:
        rep = grade.validate_task(t)
        if not rep["valid"]:
            bad.append((t.id, rep["reasons"]))
            if not quiet:
                print("  INVALID  %-24s %s" % (t.id, "; ".join(rep["reasons"])))
        elif not quiet:
            print("  ok       %-24s (%s)" % (t.id, t.difficulty))
    return bad


# ------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(prog="sica")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("pin")
    p.add_argument("--profile", default="smoke")

    p = sub.add_parser("validate-bench")
    p.add_argument("--profile", default="smoke")
    p.add_argument("--fixtures", action="store_true")
    p.add_argument("--hard", action="store_true", help="use the tasks_hard set")
    p.add_argument("--tasks", default=None,
                   help="benchmark subdir under bench/ (e.g. tasks_axis2)")

    p = sub.add_parser("lock-grading",
                       help="write the committed grading-asset hash-lock (T1)")
    p.add_argument("--hard", action="store_true", help="use the tasks_hard set")
    p.add_argument("--tasks", default=None,
                   help="benchmark subdir under bench/ (e.g. tasks_axis2)")
    p = sub.add_parser("leakscan",
                       help="verify grading-asset containment (T1)")
    p.add_argument("--hard", action="store_true", help="use the tasks_hard set")
    p.add_argument("--tasks", default=None,
                   help="benchmark subdir under bench/ (e.g. tasks_axis2)")

    p = sub.add_parser("estimate")
    p.add_argument("--profile", default="smoke")

    p = sub.add_parser("verify")
    p.add_argument("--seed", default="v1")

    p = sub.add_parser("report")
    p.add_argument("--profile", default="smoke")
    p.add_argument("--seed", default="s1")
    p.add_argument("--ledger", default=None)

    p = sub.add_parser("run")
    p.add_argument("--profile", default="smoke")
    p.add_argument("--backend", default="claude_cli",
                   choices=["claude_cli", "anthropic_api", "stub"])
    p.add_argument("--seed", default="s1")
    p.add_argument("--yes", action="store_true",
                   help="session approval granted (directive section 5)")
    p.add_argument("--max-cost", type=float, default=None,
                   help="hard session cost cap in USD (budget-exhaustion halt)")
    p.add_argument("--overrides", default=None,
                   help="JSON of profile overrides (sizes, K, generations)")
    p.add_argument("--halt-on-adopt", dest="halt_on_adopt",
                   action="store_true", default=None,
                   help="halt for approval if a gate adoption fires (T8); "
                        "default ON for smoke/micro")
    p.add_argument("--no-halt-on-adopt", dest="halt_on_adopt",
                   action="store_false",
                   help="run adoptions unattended (directive default)")
    p.add_argument("--hard", action="store_true",
                   help="run on the harder tasks_hard benchmark")
    p.add_argument("--tasks", default=None,
                   help="benchmark subdir under bench/ (e.g. tasks_axis2)")

    args = ap.parse_args(argv)
    subdir = (getattr(args, "tasks", None)
              or ("tasks_hard" if getattr(args, "hard", False) else None))
    lock_path = config.grading_lock_for(subdir)

    if args.cmd == "pin":
        cfg = config.make_config(args.profile, "claude_cli", "pin")
        bench = _benchmark(cfg)
        iso_ok, iso_why = sandbox.probe_isolation()
        print("benchmark pin :", bench.pin())
        print("isolation     :", iso_ok, "(%s)" % iso_why)
        print("swebench      :", swebench.availability())
        return 0

    if args.cmd == "validate-bench":
        cfg = config.make_config(args.profile, "stub", "val")
        bench = (LocalSuite(tasks_root=FIXTURES_ROOT) if args.fixtures
                 else _benchmark(cfg, subdir=subdir))
        tasks = bench.all_tasks()
        print("validating %d tasks (%d repos)..."
              % (len(tasks), len({t.repo for t in tasks})))
        bad = validate_tasks(tasks)
        print("\n%d/%d tasks valid" % (len(tasks) - len(bad), len(tasks)))
        return 1 if bad else 0

    if args.cmd == "lock-grading":
        from . import leakscan
        cfg = config.make_config("smoke", "stub", "lock")
        bench = _benchmark(cfg, subdir=subdir)
        lock = leakscan.write_lock(bench, lock_path)
        print("wrote grading-asset lock: %d tasks, combined_sha=%s\n  -> %s"
              % (lock["n_tasks"], lock["combined_sha256"][:16], lock_path))
        return 0

    if args.cmd == "leakscan":
        from . import leakscan
        cfg = config.make_config("smoke", "stub", "scan")
        bench = _benchmark(cfg, subdir=subdir)
        reach = leakscan.reachability_scan(bench)
        ok, reasons = leakscan.verify_lock(bench, lock_path)
        print("reachability scan: %s (%d tasks)"
              % ("OK" if reach["ok"] else "FAIL", reach["checked"]))
        for r in reach["reasons"]:
            print("  - %s" % r)
        print("hash-lock verify : %s" % ("OK" if ok else "FAIL"))
        for r in reasons:
            print("  - %s" % r)
        return 0 if (reach["ok"] and ok) else 1

    if args.cmd == "estimate":
        cfg = config.make_config(args.profile, "claude_cli", "est")
        print_approval_block(args.profile, cfg, _benchmark(cfg))
        return 0

    if args.cmd == "report":
        from . import report as report_mod
        return report_mod.report(args.profile, args.seed, args.ledger)

    if args.cmd == "verify":
        from .stubmodel import stub_model
        cfg = config.make_config("verify", "stub", args.seed)
        bench = _benchmark(cfg, verify=True)
        print("validating verify fixtures...")
        bad = validate_tasks(bench.all_tasks())
        if bad:
            raise SystemExit("verify fixtures are invalid: %s" % bad)
        model = ModelClient(backend="stub", stub_fn=stub_model)
        eng = Engine(cfg, bench, model, _dirs(),
                     run_id=binascii.hexlify(os.urandom(3)).decode())
        summary = eng.run(_load_incumbent())
        print("\nVERIFY SUMMARY:", summary)
        return 0

    if args.cmd == "run":
        overrides = None
        if args.overrides:
            import json
            overrides = json.loads(args.overrides)
        cfg = config.make_config(args.profile, args.backend, args.seed,
                                 overrides)
        if subdir:
            cfg["benchmark_subdir"] = subdir
        bench = _benchmark(cfg, subdir=subdir)
        est = print_approval_block(args.profile, cfg, bench)
        if subdir:
            print("  BENCHMARK SET    : %s (harder)" % subdir)
        if args.backend != "stub" and not args.yes:
            raise SystemExit(
                "\nREFUSED: real-backend run needs session approval. Re-run "
                "with --yes and an approved --max-cost after reviewing the "
                "approval block above (directive section 5).")
        cap = args.max_cost if args.max_cost is not None else \
            (est["cost_high_usd"] * 1.5 if args.backend != "stub" else None)
        if args.backend == "stub":
            from .stubmodel import stub_model
            model = ModelClient(backend="stub", stub_fn=stub_model)
        else:
            model = ModelClient(backend=args.backend,
                                model=cfg["model_pinned"],
                                temperature=cfg["model_temperature"])
        print("\nvalidating the %d split tasks..." % (cfg["n_train"]
                                                      + cfg["n_heldout"]))
        train, heldout = bench.split(cfg["seed"], cfg["n_train"],
                                     cfg["n_heldout"])
        bad = validate_tasks(train + heldout, quiet=True)
        if bad:
            raise SystemExit("split contains invalid tasks: %s" % bad)
        print("all split tasks valid; session cost cap = %s\n"
              % ("$%.2f" % cap if cap else "none"))
        # T8: default to halting on any gate adoption for smoke/micro; the PI
        # must keypress to accept a self-modification. Overridable explicitly.
        halt_on_adopt = args.halt_on_adopt
        if halt_on_adopt is None:
            halt_on_adopt = args.profile in ("smoke", "micro")
        run_id = binascii.hexlify(os.urandom(3)).decode()
        eng = Engine(cfg, bench, model, _dirs(), session_cost_cap=cap,
                     run_id=run_id, halt_on_adopt=halt_on_adopt,
                     grading_lock_path=lock_path)
        print("T8 adoption policy: %s\n"
              % ("HALT for approval on any gate adoption"
                 if halt_on_adopt else "adopt unattended"))
        summary = eng.run(_load_incumbent())
        print("\nRUN SUMMARY (run_id=%s):" % run_id, summary)
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(main())
