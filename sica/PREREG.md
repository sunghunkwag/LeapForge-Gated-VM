# PREREG — SICA smoke, pre-registered before any metered run

Written and committed BEFORE the first real-model (metered) generation loop.
No capability/generation run with a real model has occurred at commit time; the
only end-to-end runs so far use the deterministic **stub** backend at $0 (no
API), plus a one-off 3-call model-backend **connectivity probe** ($0.003432,
disclosed) that produced no generations and no curve. Metering — the per-task
token/tool/step budget accounting that yields the held-out curve — restarts
from zero with the smoke, which will run only after this file is committed and
after the PI approves §5.

## 0. The one metric

Held-out solve rate, generation over generation, going up. Not p-values, not
defensibility. GEN0-vs-best held-out delta is the headline.

## 1. Substrate (pinned before the run)

- Base model (the solving agent): **claude-haiku-4-5-20251001**, pinned, no
  mid-run swap. Temperature 0 is *requested*; the `claude` CLI backend exposes
  no temperature flag, so for that backend temperature is the provider default
  — recorded as a substrate caveat, not silently assumed.
- Benchmark: **localsuite**, 26 tasks / 13 repos, content-pinned
  (`runner/bench/localsuite.py::pin`); grading assets separately hash-locked
  (`runner/bench/GRADING_ASSETS.lock.json`, combined_sha `a74c9fd04dc213e4`).
- Split: repository-disjoint, fixed per seed. Smoke: 15 train / 10 heldout.
- Tournament K, generations, budgets: set at §5 approval (smoke default K=2,
  3 generations, per-task caps in `config.DEFAULT_TASK_BUDGET`).

## 2. Pre-registered prediction

**Default expectation (the honest null):** at this scale — a single small model
(Haiku), K=2 candidate scaffolds per generation, 3 generations, ~25 tasks, and
the T8 keypress that HALTS the run on the first adopted change — the held-out
curve most likely stays **flat**, because (a) at most one self-modification can
be adopted before the run halts for approval, and (b) one scaffold edit from a
small model on a tiny task set is unlikely to move a repository-disjoint
held-out score outside sampling noise. A flat curve is a legitimate result and
will be reported as one ("self-modification did not improve held-out capability
at this scale"), not dressed up.

**The live alternative:** the gate adopts a candidate that addresses a
recurring failure mode (e.g. the agent not inspecting the failing test before
editing, or not localising the faulty function), and that adopted scaffold —
scored on the *repository-disjoint* held-out slice it never trained on — solves
strictly more held-out tasks than GEN0. Because T8 halts the smoke at the first
adoption, the smoke can demonstrate at most the GEN0→GEN1 step of this; the
multi-generation compounding claim is explicitly NOT tested by the smoke and is
deferred to a PI-supervised `full` run.

## 3. Contamination disclosures (self-authored benchmark)

The benchmark is self-authored rather than a pinned public one because the
maintained public standard (SWE-bench Verified) needs multi-GB per-instance
Docker images and network to registries this sandbox forbids, and an unattended
smoke cannot build them within the token/time budget. Consequences, stated
plainly:

- **Authoring model ≠ solving agent model.** The tasks were authored by the
  session model at authoring time (**claude-fable-5**) and by a deterministic
  hand-written generator; the solving agent is **claude-haiku-4-5-20251001**.
  They are different models. Residual risk: both are Claude models and may share
  stylistic priors, so a task authored by one Claude could be marginally easier
  for another Claude than for an unrelated solver. This is disclosed, not
  eliminated. The held-out *split* (repository-disjoint) still prevents the
  ENGINE from memorising repo-specific quirks, which is the contamination that
  would fake a *curve*; author/solver shared-lineage would at most shift the
  absolute level, not manufacture a generation-over-generation rise.
- **Mitigation (T1), implemented and verified:** grading assets — hidden
  fail→pass tests, gold patches, and each `meta.json` — are held OUTSIDE the
  agent's read scope, hash-locked, and covered by the source-scan control:
  - the agent workdir is a copy of `repo/` only; `hidden/`, `gold/`, `meta.json`
    are never materialised into it (G-isolate);
  - the scaffold subprocess runs in a **mount namespace** that hides
    `runner/bench/tasks`, `runner/bench/fixtures`, `ledger`, `memory`,
    `archive`, `runs` behind a tmpfs — so even a Python-sandbox escape to `os`
    reads nothing (verified by `test_mount_ns_blocks_os_escape_read_of_grading_assets`);
  - `leakscan.reachability_scan` fail-closes the run if any grading asset is
    within the workdir scope or a hidden grading assertion appears in a source
    file; `leakscan.verify_lock` fail-closes on any drift from the committed
    hash-lock. Both run at GENESIS before any metered work.
  - Authoring transcripts live under `~/.claude/.../subagents/workflows`,
    outside the repository tree and every workdir; they are never readable by
    the agent.

## 4. Transfer family

The transfer / one-shot read is **SWE-bench Verified** (public, human-filtered,
real GitHub issues on large real repos), pinned in `runner/bench/swebench.py`,
and **not self-authored**. It is therefore disjoint from localsuite in task
STYLE (real multi-file repos + real issues vs synthetic single-file mini-repos),
not merely in repository identity. It is host-gated (needs docker + images) and
**does not run in the smoke** — the adapter refuses rather than fabricating a
score.

**Signature-check downgrade:** any cross-style / transfer "signature" from the
earlier directive is NOT claimed from self-authored data. A transfer capability
statement will be made only from the public SWE-bench read, and only when that
backend actually runs on a provisioned host. The smoke asserts nothing about
transfer.

## 5. Human-in-the-loop (T8)

The smoke runs unattended ONLY while zero self-modifications are adopted. If any
generation's adoption gate fires (a candidate strictly beats the incumbent on
the train slice), the engine writes a `PENDING_ADOPTION` record and **halts for
a PI keypress** before self-modifying; it does not score the pending candidate
on held-out. So the smoke either (a) completes with no adoption and a
by-construction-flat curve, or (b) halts at the first gate firing awaiting
approval. This is enforced by `halt_on_adopt` (default ON for the smoke/micro
profiles).

## 6. Guardrails (the price of the number meaning anything)

G-isolate, G-heldout, G-sandbox, G-budget — see `README.md`. They are enforced
structurally (mount + network namespaces, restricted-builtins scaffold, brokered
`ctx`, hidden-test grading, per-op meters) and covered by the pytest guardrail
suite. Cutting any of them would forge the gauge; they stay.
