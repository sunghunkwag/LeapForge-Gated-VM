# LeapForge-Gated-VM — Expedition XVIII

**Context-sensitive gated path induction on a certified difficulty ladder.
Zero dependencies. Deterministic to the bit. Self-auditing. Every claim
paired with the control that could kill it.**

One file: [`leapforge_gated.py`](leapforge_gated.py) (pure Python 3 standard
library — no numpy, no torch, no network, no wall clock). One replayable
smoke ledger: [`runs/gate_9be260d514.jsonl`](runs/gate_9be260d514.jsonl).

```bash
python3 leapforge_gated.py audit            # AST self-audit + source sha256
python3 leapforge_gated.py test             # 18-test honesty suite (G1-G5)
python3 leapforge_gated.py build            # enumerate + prove the ladder
python3 leapforge_gated.py battery --seeds 1-40
python3 leapforge_gated.py report
python3 leapforge_gated.py replay           # bit-identical re-simulation
```

Verified state of this exact source (sha256 `cc78a281595b8db1...`): audit
pass, 18/18 tests, and the included 3-seed smoke ledger re-simulates
bit-identically (`replay --profile smoke`). The smoke ledger is a machinery
proof, **not** a finding: n = 3 seeds is underpowered by this project's own
standard (n >= 40), and every smoke contrast sits inside the noise floor.

---

## 1. Project lineage and provenance map

This file is the fourth harness in a lineage whose method was forged by its
own failures. The sequence that matters:

| expedition | question | verdict that shaped this repo |
|---|---|---|
| VI | does a learned prior transfer to held-out domains? | yes, small: **+9.3pp above the null-control floor, p = 0.0001** (after two retractions, below) |
| VII | do richer *static* containers (bigram/trigram) help? | **flat ladder**: BIGRAM − META = −0.067 (p = 0.49). First attempt invalidated by a raw-count zero-probability bug — a 480-run study was measuring memorization. Three permanent guardrails date from this failure. |
| VIII | learned abstractions as atomic tokens? | **worse, decisively**: ABSTRACT − PRIOR = **−0.433, p = 0.00002** (survives Bonferroni); broke 39.4% of what cold search already solved |
| X | is "breakage" even real? | the zero-effect null (`COLD2`, same method, different seed) posts 13.7% "rescue" and 20.8% "breakage" on its own. Two headline findings were retracted against this floor. **COLD2 is mandatory in every battery since.** |
| XI | does self-improvement *compound*? | **no**: recursion premium ROUND5 − ROUND1_5X = **−0.025, p = 0.876** against a compute-matched control (960 runs) |
| XII | why did eleven expeditions fail? | **the substrate had no difficulty gradient**: cold search solved 10–12 of 12 at every generating length; 38% of "hard" tasks were re-solved by the same solver with a different seed. They were unlucky, not hard. |
| XIV | build a substrate that *has* a gradient | pipelines over 20 unary list primitives; observational-equivalence pruning is valid, so **difficulty = minimal depth is computed, not assumed**. 20 / 294 / 3,858 / 47,684 behaviours at depths 1–4; per-task certification rejects the 10–25% of tasks that admit a secretly shorter solution. Monotone at every budget; every rung climbable. |
| XV (`leapforge_unified`) | re-pose XI's compounding question on the certified ladder | harness verified (replay bit-identical); full battery pending |
| XVI (`leapforge_plasticity`) | 2D transition manifold `W[prev][next]` + runtime plasticity trace | guardrails G1–G3 wired as permanent self-tests; smoke contrasts inside the floor |
| XVII (`leapforge_composition`) | dynamic macro compilation (registry + virtual runtime, G4) | smoke direction matched VIII's historical negative; deployment telemetry added so a lift without macro use cannot be misattributed |
| **XVIII (this repo)** | **state-contextual gating: a 3D manifold conditioned on the runtime list state** | pre-registered against the container-richness precedent; the 2D baseline is the *same engine* with a constant gate function |

The lineage's one transferable law: **any rate measured against a single
stochastic reference run is meaningless without a same-method,
different-seed null control.** Every number this repo prints is read
against that floor.

## 2. Mathematical formulation of 3D gating

### 2.1 State invariant (the gate)

For a list state $x$ produced mid-pipeline, `get_state_context(x)` returns
the first matching class (total, deterministic, $O(n)$):

$$
g(x) \;=\;
\begin{cases}
0 & |x| \le 1 \\
1 & x_i \ge x_{i-1}\ \forall i \quad\text{(monotone non-decreasing)} \\
2 & \max(x) - \min(x) \le 15 \quad\text{(compact value range)} \\
3 & \text{otherwise}
\end{cases}
$$

The byte domain (values in $[0,255]$) has no sign, so order/range
invariants replace polarity-style predicates. A runaway intermediate state
is defined as `[]` (gate 0) from that point on; every primitive is total on
`[]`.

### 2.2 Transition manifold and sampling

The manifold is a 3D weight table over token space $T$ (20 primitives plus
registered macro tokens) with depth-keyed start rows:

$$
W \in \mathbb{R}_{>0}^{\,G \times (T \cup S) \times T},
\qquad G = \{g_0,\dots,g_3\},\quad S=\{\langle S_1\rangle .. \langle S_4\rangle\}
$$

The sampler walks the pipeline while tracking the list state on a reference
input (the task's shortest train example). At each step the next token is
drawn from the **active cross-section** by floor-weighted roulette:

$$
P(\text{next}=c \mid g, \text{prev}=r) \;=\;
\frac{W[g][r][c]}{\sum_{c' \in T} W[g][r][c']}
$$

Every edge carries a floor weight of $1.0$ (guardrail **G1**: no zero
probabilities, anywhere, including rows/columns allocated dynamically when
a macro is registered).

### 2.3 Plasticity update (the active cross-section only)

Within one task's search, a local copy $W_{loc}$ decays toward its base
each generation and is reinforced on every strict improvement of the
running best partial fitness $\Delta f = f - f_{best} > 0$, applied to the
traced gated path of the improving program:

$$
W_{loc}[g][r][c] \;\leftarrow\; \lambda\, W_{loc}[g][r][c] + (1-\lambda)\, W_{base}[g][r][c]
$$

$$
W_{loc}[g_i][r_i][c_i] \;\mathrel{+}=\; \eta \cdot \Delta f \cdot \xi
\quad \text{for each edge } (g_i, r_i, c_i) \text{ on the improving path}
$$

with $\lambda = 0.90$, $\eta = 0.5$, and $\xi = \text{level}/4$ — the
task's **certified minimal depth**, the one place "distance on the
difficulty rungs" is a computed quantity (enumeration-proven, per-task
re-certified) rather than an estimate. Decaying toward the base (not zero)
preserves the G1 floor under arbitrarily long decay/reinforce sequences.

Macro admission is separate from the trace: a primitive window (length
2–3) is compiled into a token only if its cumulative fitness weight is
$\ge \theta_{up} = 2.0$ across $\ge 2$ distinct programs (registry cap 6,
no nesting — guardrail **G4**: expansion is primitive-only, capped, and
behaviour-identical to the token form).

### 2.4 Guardrails wired into the test suite

| id | invariant | origin |
|---|---|---|
| G1 | no zero probabilities across every gate slice, ever | Exp VII's sealed-space bug |
| G2 | fitted-manifold entropy does not collapse | Exp VII (0.21-bit collapse) |
| G3 | reinforcement strictly increases the reinforced path's probability | XVI |
| G4 | macro expansion sound, capped, behaviour-preserving; ladder and `certify()` live in primitive space, untouched | XVII |
| G5 | the gate extractor is total, deterministic, in-range (fuzzed) | XVIII |

## 3. Experimental protocol: the isolation

### 3.1 One engine, one changed variable

The decisive design property: **the 2D baseline is not a separate
implementation.** `COMP5` runs the identical engine with `gate_const`
(every state maps to gate 0), which collapses the manifold to one slice.
Sampling walk, mutation, plasticity, mining, fitting, and the
counterfactual gate are shared line-for-line. Therefore:

$$
\text{GATING LIFT} \;=\; \text{GATE5} - \text{COMP5}
$$

isolates exactly one variable — whether conditioning on the runtime state
invariant buys anything.

### 3.2 Conditions (all chain arms train on the SAME source tasks at the
SAME total compute)

| condition | engine | knowledge |
|---|---|---|
| COLD | 3D gated | none (uniform manifold, empty registry) |
| COLD2 | 3D gated | none — only the PRNG stream label differs: **the noise floor** |
| GATE5 | 3D gated | manifold + macros after 5 recursion rounds |
| GATE1_5X | 3D gated | ONE round at 5x budget: same total source compute, zero recursion |
| GATED7 | 3D gated | like GATE5, but every refit + macro admission must beat the incumbent in a counterfactual A/B at equal budget on identical PRNG streams (atomic accept/reject) |
| COMP5 | constant gate (2D) | Expedition XVII's container, re-instantiated for pairing |
| PLASTIC5 | constant gate (2D) | registry pinned empty (no macros) |
| UNIGRAM5 | 1D static | Expedition XV's container |

Capability = exact output on train **and** on longer held-out inputs, at
certified levels 3 and 4, on a per-seed target split of behaviours
disjoint from the source split. One unit per (config, condition, seed);
reruns are refused by the ledger.

### 3.3 Statistics and honesty machinery

Paired sign-flip permutation tests (20,000 permutations), percentile
bootstrap CIs (5,000 resamples), Holm correction across the
treatment-vs-COLD family. Every contrast is read against the COLD2 floor.
Deployment telemetry is reported per condition — registry size, solved
tasks containing a macro token, solved tasks whose traced path crosses
>= 2 distinct gates, deepest expanded solution — because **a lift without
multi-gate deployment is noise, not mechanism**.

Pre-registered prediction (quoted from the source): GATING LIFT sits
inside the noise floor — container richness dies a third time, and that is
recorded as the finding. The live alternative requires BOTH GATE5 − COMP5
above the floor AND multi-gate traces in solved frontier tasks.

### 3.4 Known accounting caveat (stated, not hidden)

The budget unit is fitness evaluations — the lineage's accounting unit.
The gated sampler performs additional $O(\text{len})$ list operations per
proposed token that flat samplers do not, so wall-compute is not exactly
matched across engines; within-engine contrasts (GATE5 vs GATE1_5X vs
GATED7) are unaffected. Baselines are re-instantiated in this file for
paired comparison and are not bit-compatible with the XVI/XVII files.

## 4. Determinism and audit

- All randomness flows through `XorShift64Star` streams seeded by SHA-256
  of human-readable text tags; identical tags yield identical streams,
  which is what makes every A/B arm a true counterfactual.
- `audit` parses the file's own AST: forbidden imports (random, numpy,
  torch, time, pickle, threading, ...), dynamic eval/exec, a line cap, and
  a banned-claim-word token scan must all pass; the source sha256 is
  embedded in every ledger's GENESIS record, so `replay` doubles as a
  code-identity proof.
- The ledger is append-only and hash-chained
  (`hash = sha256(prev_hash + canonical_json(body))`); `replay` rebuilds
  every chain arm and re-runs every evaluation unit, requiring
  bit-identical bodies and hashes.

## 5. Repository layout

```
leapforge_gated.py            the complete engine + tests + CLI (one file)
runs/gate_9be260d514.jsonl    3-seed smoke ledger (machinery proof; replayable)
LICENSE                       MIT
```

## 6. Scope, honestly

The substrate is 20 unary list primitives at CPU-poverty scale — not
language, not perception. Nothing here claims general capability. The
repository's contribution is a measurement discipline: certified
difficulty labels, mandatory null controls, compute-matched recursion
controls, pre-registered predictions, atomic gated admission, and
bit-identical replay — applied to one sharply posed question about
state-conditioned search policies.
