# SICA smoke — results (§7 report)

Two metered runs, pinned `claude-haiku-4-5-20251001`, K=2, 3 generations, T8
keypress-on-adoption ON, run after `PREREG.md` was committed. Total metered
spend across both runs: **$6.66** (of a $20 approved cap). No held-out result
ever fed back into proposals or the gate (G-heldout); grading used hidden tests
the agent never saw (G-isolate); the self-editing scaffold ran net+mount
namespaced with grading assets hidden by tmpfs (G-sandbox); per-op meters
enforced hard caps (G-budget). All four guardrails held on both runs.

## Run 1 — `localsuite` (26 tasks / 13 repos): CEILING

| gen | held-out | adopted |
|-----|----------|---------|
| g0  | 100.0%   | baseline |
| g1  | 100.0%   | no |
| g2  | 100.0%   | no |
| g3  | 100.0%   | no |

GEN0 already solved **15/15 train and 10/10 held-out**. A candidate cannot
strictly beat a perfect incumbent, so the gate correctly kept the incumbent and
the curve is flat at 100% **by construction** — a benchmark-saturation result,
not evidence about self-modification. Cost $2.50.

## Run 2 — `tasks_hard` (26 tasks / 13 repos, with headroom): NO ADOPTION

Harder benchmark: each repo's `t1` is context-dependent — the fix needs values
defined in a **non-editable** file, and the issue withholds them, so the
editable-only GEN0 scaffold structurally cannot solve them. `t2` tasks are
direct GEN0-solvable bugs. The 15/10 split lands 8/15 train and 5/10 held-out as
context-dependent.

| gen | held-out | solved/n | adopted |
|-----|----------|----------|---------|
| g0  | 40.0%    | 4/10     | baseline |
| g1  | 40.0%    | 4/10     | no |
| g2  | 50.0%    | 5/10     | no |
| g3  | 40.0%    | 4/10     | no |

GEN0 held-out = **40%** — real headroom this time. The failure-driven proposer
**correctly diagnosed the failure mode** and proposed the right kind of change
(`enable-grep-context`, `expand-test-output-visibility`) across every
generation. But **no candidate ever beat the incumbent on train** (each solved
8/15, same as GEN0), because GEN0's context-gathering greps for the editable
file's own name, not for the withheld config values — so enabling it does not
actually extract them. The gate therefore **correctly adopted nothing**.

### The +10pt "best" is NOISE, and the engine correctly refused to bank it

Because no change was adopted, the **same GEN0 scaffold** was scored every
generation. The held-out curve's wiggle (40 → 40 → 50 → 40) is **model sampling
noise** on a fixed scaffold — Haiku is non-deterministic (the CLI backend
exposes no temperature flag). The apparent "best 50% vs GEN0 40% = +10pt" is
sampling variance, **not** a capability gain. `report.py` attributes it as such.

This is the guardrails doing their job: the adoption gate declined to bank a
change that did not demonstrably help on train, and the held-out discipline
kept the noise from being mistaken for improvement. It is the difference
between measuring the temperature and optimising the thermometer. Cost $4.08.

## Honest conclusion

- **The engine is validated end-to-end on real metered runs.** Both runs
  exercised the full pipeline — failure-driven proposals, tournament gate,
  improvement memory, archive, quality-diversity escape, T8, per-op meters, and
  net+mount-namespace isolation with fail-closed T1 containment — against the
  live pinned model.
- **Self-modification did NOT lift held-out capability at this scale.** On the
  saturated benchmark there was no headroom; on the benchmark with headroom the
  proposer identified the right failure mode but produced no candidate that beat
  the incumbent, so nothing was adopted and held-out did not rise. Reported
  plainly, per directive §7/§9 — a flat/noise result is a legitimate outcome
  and is not dressed up.
- **What would move the curve** (deferred, needs PI approval for more spend): a
  stronger GEN0 context tool (or a proposer candidate that reads the *contents*
  of non-editable files, not just greps names), a larger tournament (K=4), and
  more generations, on the headroom benchmark. The T8 keypress means the first
  candidate that does beat the incumbent will halt for approval rather than
  self-modify unattended.

Artifacts (auditable): `results/smoke_s1_*` (run 1) and
`results/smoke_hard_s1_*` (run 2) — each run's hash-chained ledger, improvement
memory, and full log.
