# SICA — a self-improving coding-agent engine

SICA runs a **self-improvement loop** on a coding agent and watches **one
number**: the held-out solve rate, generation over generation. The agent
rewrites its own *scaffold* — its system prompts, its plan→act→verify loop, its
retry policy, and its tools — and a selection gate keeps a change only when it
strictly beats the incumbent. The point is **real capability gain**, measured
on tasks the agent never trains on and graded by tests it can never read.

> This is the performance-mode engine described in the project directive. It
> deliberately keeps the three things without which the number would be a lie —
> a repository-disjoint held-out split, the adoption gate, and test/gold
> isolation + sandbox — and drops the statistics-for-publication machinery
> (noise floor, permutation tests, bootstrap CIs, pre-registration) that proves
> a result but does not *produce* one.

## The one metric

Everything serves **held-out solve rate going up across generations**. A flat
curve is a legitimate outcome and is reported as one, not dressed up.

## How a generation works (the loop)

1. the **incumbent** scaffold attempts the TRAIN slice at a fixed, metered
   budget;
2. its own **failing transcripts** plus a held-out-stripped **improvement
   memory** drive **K candidate scaffolds**, each targeting a different failure
   mode, with a rationale and an expected-effect prediction;
3. the **adoption gate** runs each candidate against the incumbent on the *same*
   train tasks / seeds / budget and keeps the **strict winner** (a tie goes to
   the incumbent) — this gate is the engine's selection operator;
4. the winner is scored on the **HELD-OUT** slice — this is the curve, and it
   never feeds back into proposals or the gate;
5. the change, its prediction, and its measured train+held-out deltas are
   appended to the improvement memory and the scaffold archive; the ledger is
   snapshotted; the curve is printed.

If held-out stalls for two generations the engine performs a
**quality-diversity escape**: it branches from the best *prior* archived
scaffold (chosen by TRAIN score, so selection stays held-out-blind) along a
failure mode it has not recently tried, instead of grinding a local optimum.

## The four guardrails (why each is load-bearing)

These are not ceremony — each is what makes the number *mean* capability.

- **G-isolate** — grading tests and gold patches are never placed in the
  agent's workdir; the grader overlays only the task's declared editable files
  into a throwaway eval copy, then runs the hidden tests. A scaffold cannot
  read the answer, and cannot pass by side-effect (a stray `conftest.py`, an
  edited public test) because none of that survives into the eval copy.
- **G-heldout** — proposals and the gate never see held-out results; the
  improvement memory's proposer view strips the held-out deltas at the data
  layer.
- **G-sandbox** — the self-editing scaffold runs in a **no-network subprocess**
  (`unshare -n`) with a restricted builtins namespace (no `open`, `os`,
  `eval`, `__import__` of anything outside a tiny stdlib allowlist, no dunder
  gadgets — statically enforced by an AST audit). Its *only* route to the model,
  the filesystem, or a test run is the `ctx` object, every call of which the
  trusted parent brokers, meters, confines to the workdir, and can refuse.
- **G-budget** — per-task token / tool-call / step / wall-clock meters with
  hard caps, checked *before* every spend; a generation that balloons past a
  multiple of the established per-generation spend auto-halts.

The loop auto-halts on: budget exhaustion, a generation over-spending, held-out
regression for N consecutive generations, or any scope-escape / grading-asset
access attempt (halt + preserve ledger).

## Layout

```
sica/
  sica.py                 CLI entrypoint
  runner/                 the trusted harness — the agent cannot edit this
    config.py             pinned model, benchmark pins, budgets, profiles
    ledger.py             append-only hash-chained ledger
    audit.py              static scaffold audit (G-isolate/G-sandbox, compile-time)
    restricted.py         safe-builtins namespace for scaffold code
    meters.py             per-task hard caps (G-budget)
    model.py              model client: claude_cli / anthropic_api / stub backends
    sandbox.py            unshare -n executor (G-sandbox, runtime)
    broker.py             serves the scaffold subprocess; enforces all four guardrails
    ctx_client.py         the ctx capability object the scaffold sees
    scaffold_runner.py    subprocess bootstrap that hosts the untrusted scaffold
    grade.py              sealed grading with hidden tests (G-isolate, runtime)
    harness.py            one task attempt: workdir -> broker -> grade
    bench/                Task/Benchmark, repo-disjoint split, localsuite, swebench pin
    proposer.py           failure-driven, memory-informed K-candidate proposer
    gate.py               the adoption gate (strict-winner selection)
    memory.py             cross-generation improvement memory (heldout-stripped view)
    archive.py            scaffold archive + quality-diversity escape
    evaluate.py           parallel scaffold evaluation over a slice
    engine.py             the generation loop + auto-halts
    report.py             the section-7 held-out report
  scaffold/               the AGENT's self-modifiable seed (GEN0); the engine rewrites this
  memory/ archive/ ledger/ runs/   runtime artifacts (git-ignored, regenerated)
  tests/                  guardrail + machinery pytest suite
  tools/validate_task.py  standalone task validator (fail->pass transition)
```

## The benchmark

The engine loop runs on **localsuite**: real, self-contained, repository-disjoint
Python bug-fix tasks, each with an issue, a buggy repo, public tests the agent
may run, a gold patch, and **hidden fail→pass grading tests** the agent cannot
see. Every task's fail→pass transition is validated before use (on the buggy
snapshot the hidden tests fail and the regression guard passes; on gold both
pass), and the whole suite is content-pinned.

**Why not SWE-bench Verified for the loop?** SWE-bench Verified is the
maintained real-repo standard and is *pinned here* (`bench/swebench.py`) as the
`full`/transfer backend, but each instance needs a multi-GB Docker image and
network to registries this sandbox does not permit, and an unattended smoke
cannot build hundreds of them inside the token/time budget. localsuite keeps
every property that makes the score mean capability while running fully offline
and deterministically so the engine can actually iterate. The SWE-bench adapter
*refuses to run* (rather than fabricating a score) when the host cannot provide
the images — a number must mean capability or not be produced at all.

## Running it

```bash
# $0 deterministic end-to-end check of the whole engine (stub model, no network)
python3 sica.py verify

# guardrail + machinery unit/integration tests
python3 -m pytest tests -q

# benchmark integrity + pins + isolation status
python3 sica.py validate-bench --profile smoke
python3 sica.py pin --profile smoke

# the section-5 session approval block (model, benchmark, budgets, cost estimate)
python3 sica.py estimate --profile smoke

# run the engine (real model; needs the one session approval + a cost cap)
python3 sica.py run --profile smoke --backend claude_cli --yes --max-cost 8

# the section-7 held-out report
python3 sica.py report --profile smoke --seed s1
```

The base model is pinned (`claude-haiku-4-5-20251001`) and never swapped
mid-run. Temperature 0 is *requested*; the `claude` CLI backend exposes no
temperature flag, so for that backend temperature is the provider default —
logged honestly as a substrate caveat rather than silently assumed. Model
sampling is the one non-deterministic layer; all *engine* randomness (task
selection, splits, tie-breaks) flows through SHA-seeded streams, so task sets
are fixed per seed and the gate compares candidates against the incumbent on
identical tasks.
