"""Fixed substrate: pinned model, benchmark pins, budgets, profiles.

Directive section 3 -- "so gains are real, not drift". The model string is
pinned and never swapped mid-run; the benchmark and its split are pinned per
seed; all budgets are hard caps enforced by the meters (G-budget).
"""

import copy
import hashlib
import json
import os

# --- the one place the base model is named. No mid-run swap. -----------------
# Pinned string. temperature is requested as 0 on every backend that exposes
# it; the claude-cli backend does not expose a temperature flag, so for that
# backend temperature is the provider default and this is logged honestly as a
# substrate caveat rather than silently assumed to be 0.
MODEL_PINNED = "claude-haiku-4-5-20251001"
MODEL_TEMPERATURE = 0.0

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # sica/
SCAFFOLD_DIR = os.path.join(REPO_ROOT, "scaffold")
RUNNER_DIR = os.path.join(REPO_ROOT, "runner")
MEMORY_DIR = os.path.join(REPO_ROOT, "memory")
ARCHIVE_DIR = os.path.join(REPO_ROOT, "archive")
LEDGER_DIR = os.path.join(REPO_ROOT, "ledger")
RUNS_DIR = os.path.join(REPO_ROOT, "runs")

# Committed hash-lock over the self-authored benchmark's grading assets (T1).
GRADING_LOCK = os.path.join(RUNNER_DIR, "bench", "GRADING_ASSETS.lock.json")


def grading_lock_for(subdir):
    """Per-benchmark-root grading-asset lock path."""
    if subdir in (None, "tasks"):
        return GRADING_LOCK
    return os.path.join(RUNNER_DIR, "bench",
                        "GRADING_ASSETS_%s.lock.json" % subdir)

# --- per-task hard caps (G-budget) -------------------------------------------
# A "tool call" is one brokered ctx.run (test execution). "steps" is one
# plan->act->verify iteration of the agent loop. Model tokens are summed from
# the backend usage reports. Any cap breach raises BudgetError; the task ends
# and counts as unsolved. A generation whose measured spend exceeds
# gen_budget_multiple x its projected spend is auto-halted (section 4/5).
DEFAULT_TASK_BUDGET = {
    "max_model_calls": 40,
    "max_model_tokens": 120000,   # input+output summed across the task
    "max_output_tokens_per_call": 8192,  # hard per-call output ceiling
    "max_tool_calls": 25,         # brokered test runs
    "max_steps": 12,              # agent loop iterations
    "max_io_ops": 2000,           # read/write/ls/grep/log calls
    "max_write_bytes": 8_000_000,  # cumulative bytes the agent may write
    "wall_seconds": 240,
}

PROFILES = {
    # ~15 train / 10 heldout, K=2, 3 generations (directive section 6 smoke).
    "smoke": {
        "profile": "smoke",
        "benchmark": "localsuite",
        "n_train": 15,
        "n_heldout": 10,
        "K": 2,
        "max_generations": 3,
        "regression_halt": 3,        # consecutive heldout regressions -> halt
        "stall_restart": 2,          # heldout flat for N gens -> QD escape
        "gen_budget_multiple": 3.0,  # >3x projected spend -> auto-halt
        "task_budget": dict(DEFAULT_TASK_BUDGET),
        "concurrency": 8,
    },
    # micro real-model proof: a few cents, proves the paid path end-to-end.
    "micro": {
        "profile": "micro",
        "benchmark": "localsuite",
        "n_train": 3,
        "n_heldout": 3,
        "K": 2,
        "max_generations": 1,
        "regression_halt": 3,
        "stall_restart": 2,
        "gen_budget_multiple": 3.0,
        "task_budget": dict(DEFAULT_TASK_BUDGET),
        "concurrency": 4,
    },
    # PI sets sizes/K/generations/budget at session start.
    "full": {
        "profile": "full",
        "benchmark": "localsuite",   # swap to "swebench" when a docker host is available
        "n_train": 40,
        "n_heldout": 25,
        "K": 4,
        "max_generations": 12,
        "regression_halt": 3,
        "stall_restart": 2,
        "gen_budget_multiple": 3.0,
        "task_budget": dict(DEFAULT_TASK_BUDGET),
        "concurrency": 8,
    },
    # deterministic, $0 verification of the whole engine (no real model).
    # 6 fixtures (3 basic + 3 SPECIAL-case): n_train=4 forces >=1 SPECIAL task
    # into train, so the stub proposer's fix is genuinely adopted by the gate.
    "verify": {
        "profile": "verify",
        "benchmark": "localsuite",
        "n_train": 4,
        "n_heldout": 2,
        "K": 2,
        "max_generations": 2,
        "regression_halt": 3,
        "stall_restart": 2,
        "gen_budget_multiple": 3.0,
        "task_budget": dict(DEFAULT_TASK_BUDGET),
        "concurrency": 4,
    },
}


def make_config(profile_name, model_backend, seed, overrides=None):
    if profile_name not in PROFILES:
        raise ValueError("unknown profile: %s" % profile_name)
    cfg = copy.deepcopy(PROFILES[profile_name])
    cfg["model_pinned"] = MODEL_PINNED
    cfg["model_temperature"] = MODEL_TEMPERATURE
    cfg["model_backend"] = model_backend
    cfg["seed"] = seed
    cfg["engine_version"] = "sica-1.0"
    if overrides:
        for k, v in overrides.items():
            if k == "task_budget" and isinstance(v, dict):
                cfg["task_budget"].update(v)
            else:
                cfg[k] = v
    return cfg


def config_sha(cfg):
    return hashlib.sha256(
        json.dumps(cfg, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:12]
