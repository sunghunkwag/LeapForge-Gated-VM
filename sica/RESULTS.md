# SICA smoke — results (metered run, §7 report)

Run: profile `smoke`, seed `s1`, backend `claude_cli`, pinned
`claude-haiku-4-5-20251001`, K=2, 3 generations, T8 keypress-on-adoption ON.
Metered run performed after `PREREG.md` was committed (`7ea9733`).

## Held-out solve-rate curve (the one metric)

| gen | held-out | solved/n | adopted | note |
|-----|----------|----------|---------|------|
| g0  | 100.0%   | 10/10    | baseline | GEN0 seed scaffold |
| g1  | 100.0%   | 10/10    | no      | 0/2 candidates beat incumbent |
| g2  | 100.0%   | 10/10    | no      | 0/2 candidates beat incumbent |
| g3  | 100.0%   | 10/10    | no      | QD escape fired (stall); 0/2 beat incumbent |

**GEN0 vs best held-out delta: +0.0 pp.**

## Honest verdict: CEILING (benchmark saturated) — not a self-modification result

GEN0 already solved **15/15 train and 10/10 held-out** with the pinned Haiku
model. A perfect baseline leaves **no headroom**: a candidate cannot *strictly*
beat a perfect incumbent, so the gate correctly kept the incumbent every
generation and the curve is flat at 100% **by construction**. This is a
**benchmark-difficulty result, not evidence about self-modification**. The
localsuite tasks — single-file bugs with explicit issue text — are too easy for
Haiku, which one-shots them from the issue.

Per the directive (§7/§9), a flat curve is reported as-is and not dressed up —
and, importantly, not mis-attributed: this flat curve says the benchmark
saturated at GEN0, **not** that self-modification failed to help.

## What the engine actually did (machinery + guardrails validated on a real run)

The run exercised every part of the engine end-to-end against the live model:

- **T1 containment, fail-closed at GENESIS**: reachability scan OK (26 tasks);
  grading-asset hash-lock verified.
- **G-sandbox**: net+mount namespaces + tmpfs hiding = OK; the self-editing
  scaffold ran with no network and no visibility of grading assets.
- **Failure-driven proposer** produced 6 distinct, genuinely sensible candidate
  scaffolds across the run, each targeting a different failure mode:
  - g1: `smart-prompt-truncation-on-retry`, `handle-crlf-line-endings`
  - g2: `file-change-tracking-tool`, `localize-failure-functions`
  - g3 (after QD restart): `include-test-source-in-prompt`,
    `enable-context-gathering-with-import-search`

  Several add NEW tools/behaviour (tool growth, §1.5). All passed the audit +
  dry-load and were evaluated by the gate — they simply could not exceed a
  perfect incumbent.
- **Adoption gate**: correctly kept the incumbent (strict-winner rule; tie →
  incumbent) — 0/2 beat incumbent each generation.
- **Quality-diversity escape**: fired at g3 on the 2-generation held-out stall,
  restarting from the best prior archived scaffold (selected by TRAIN score, so
  the restart stayed held-out-blind).
- **T8**: never triggered, because no adoption ever fired — consistent with the
  ceiling. Had a gate fired, the run would have halted for a keypress.
- **G-budget / meters**: 182 model calls, 563,420 model tokens, **$2.50**
  (within the $20 cap; above the $1.38 estimate because the agent emits full
  file contents each attempt — the rough estimator under-counts output tokens).

## Conclusion and next step

The **engine is validated on a real metered run** — every guardrail held and
every machinery component (proposal → tournament gate → memory → archive → QD
escape → T8 → meters → isolation) was exercised. The **benchmark, however, is
too easy**: it saturates at GEN0, so it cannot measure the engine's ability to
lift capability.

To actually put a number on "held-out capability going up," the held-out slice
must be hard enough that **GEN0 fails a meaningful fraction** (target ~40–70%
GEN0 solve rate). That means genuinely harder tasks — multi-file fixes,
under-specified issues, subtle logic requiring the agent to read/localize before
editing, or tasks that reward the exact scaffold improvements the proposer is
already inventing (localization, test-source inspection, context gathering).
Until the benchmark has headroom, the curve cannot move regardless of engine
quality. This is the honest, faithful reading of the smoke.
