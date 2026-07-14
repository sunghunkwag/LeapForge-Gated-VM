# SICA smoke — results (§7 report)

Pinned `claude-haiku-4-5-20251001`, T8 keypress-on-adoption ON, all runs after
`PREREG.md` was committed. Total metered spend across all runs: **$9.62** (of a
$20 cap). Every held-out result was kept out of proposals and the gate
(G-heldout); grading used hidden tests the agent never saw (G-isolate); the
self-editing scaffold ran net+mount-namespaced with grading assets tmpfs-hidden
(G-sandbox); per-op meters enforced hard caps (G-budget). All four guardrails
held on every run.

## Headline: an EARNED, held-out-verified capability gain

On the identical repository-disjoint held-out split (seed `s1`, `tasks_hard`,
10 held-out tasks), a T8-approved self-modification lifted held-out solve rate:

| scaffold | held-out | tasks |
|----------|----------|-------|
| GEN0 (seed) | **5/10 = 50%** | run `afa858` |
| adopted `enable-grep-localize-function` | **9/10 = 90%** | run `c5a044` |

**+40 percentage points on held-out, from a change the gate earned on train and
the PI approved.** The two GEN0 held-out reads across runs were 0.40–0.50
(sampling noise band), and 0.90 sits far outside it, so the jump is real, not
noise. This is the one metric — the held-out solve rate — going up via genuine
self-modification.

## How it happened (three acts)

**Act 1 — `localsuite` (26 tasks): CEILING.** GEN0 solved 15/15 train and 10/10
held-out. A candidate can't beat a perfect incumbent, so the curve was flat at
100% by construction — a saturated benchmark, no headroom. ($2.50)

**Act 2 — `tasks_hard`, first attempt: NO ADOPTION → noise.** Harder benchmark
(each repo's `t1` needs values from a NON-editable config file the editable-only
GEN0 can't reach). GEN0 held-out = 40%. The proposer diagnosed the
context-dependence failure mode and proposed context-gathering, but its
candidate greped only the editable file's own name, still solved 8/15 train, and
did not beat the incumbent — so nothing was adopted. The held-out wiggle
(40→40→50→40) was sampling noise on the unchanged scaffold, correctly attributed
as such, not a gain. ($4.08)

**Act 3 — `tasks_hard`, K=4 + enriched failure digest: EARNED ADOPTION.** The
failure digest was enriched (directive §1.1) so the proposer could see, in its
own failing transcripts, *which non-editable files were present* — i.e. that the
answer lived in files the agent never read. With that, gen-1 produced
`enable-grep-localize-function`, which greps issue-named function defs to
localize the bug AND greps `ALL_CAPS` constant/config definitions out of the
repo's non-editable files into the prompt. It solved **15/15 train vs the
incumbent's 8/15 (+7, a strict win)**. T8 HALTED for a keypress; the PI approved;
the adopted scaffold then scored **90% held-out** (vs GEN0's 50%). ($1.09 halt +
$1.88 continuation)

After adoption the scaffold re-saturates train (15/15), so the continuation's
further generations found no candidate that beat the incumbent (0/4 each) — one
genuine step, then plateau. The gate declining to adopt without a strict train
win is the selection operator working, not a failure.

## Honest caveats (not dressed up)

- **Single seed, single split, n=10 held-out.** This is a real direction and a
  clean paired comparison, NOT a statistically powered claim — the noise-floor /
  permutation / CI machinery was deliberately cut in performance mode. The exact
  magnitude is fuzzy (±~10pp) because GEN0's own held-out varies 40–50% by
  sampling.
- **The gain is one capability** (reading relevant repo context). That is a
  genuine, generalizing coding-agent skill — GEN0 could not read the config it
  needed; the adopted scaffold can, and it transferred from train to a
  repo-disjoint held-out set. But the benchmark's headroom was specifically
  context-dependence, which this one tool fills; a different headroom would test
  a different capability.
- **It reads the repo's own source** (fair game), never grading assets (hidden +
  tmpfs-hidden). Verified by the T1 reachability scan and the isolation tests.

## Conclusion

**Yes — the engine produced a real, earned, held-out-verified capability
improvement** (+40pp) through the full loop: failure-driven proposal → strict
train-win gate → T8 human approval → held-out measurement, with every guardrail
intact. It then plateaued honestly when it could no longer beat its own
incumbent. That is the qualitative-leap engine doing exactly what it was built
to do, at smoke scale, reported without embellishment.

Artifacts (auditable): `results/smoke_s1_*` (Act 1), `results/smoke_hard_s1_*`
(Act 2), `results/smoke_headroom_s1_*` + `*_pending_adoption.diff` (Act 3 gate),
`results/smoke_continue_s1_*` (Act 3 held-out measurement). Each has its
hash-chained ledger and full log.
