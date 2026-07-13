#!/usr/bin/env python3
"""
LEAPFORGE-GATED -- Expedition XVIII harness
===========================================

THE QUESTION
------------
Expedition XVII gave the sampler macros (reach) and a 2D transition
manifold (syntactic context). This file adds SEMANTIC context: the
manifold becomes 3D,

    W_trans[gate_id][prev_token][next_token]

where gate_id is a coarse discrete invariant of the LIST STATE the
partially-built pipeline has produced so far on a reference input. The
sampler's distribution therefore shifts mid-pipeline as the data
changes shape: a condition-gated execution policy, not a static
sequence preference.

THE ISOLATION (the only honest way to test a richer container)
---------------------------------------------------------------
The 2D baseline in this file is THE SAME ENGINE with a CONSTANT gate
function (one slice). Every other line of machinery -- sampling walk,
mutation, plasticity trace, mining, fitting, gating -- is shared. The
GATE5 - COMP5 contrast therefore isolates exactly one variable:
whether conditioning on the runtime state invariant buys anything.

PRECEDENT -- CONTAINER RICHNESS HAS NEVER PAID, STATED UP FRONT
---------------------------------------------------------------
Expedition VII: bigram/trigram containers -- the ladder was FLAT
(BIGRAM - META = -0.067, p = 0.49). Expedition XVI (2D + runtime
trace): not established at smoke scale. Expedition XVII (macros):
smoke direction matched the historical Exp VIII negative. A 3D gated
container is the richest container this lineage has ever proposed.

PRE-REGISTERED PREDICTION (written before any run of this file)
---------------------------------------------------------------
Default expectation: GATING LIFT = GATE5 - COMP5 sits inside the noise
floor (container richness dies a third time, and that is recorded as
the finding). The live alternative: state-conditional deployment only
matters where the data topology actually branches mid-pipeline, so a
real effect must show as GATE5 - COMP5 > floor WITH solved frontier
tasks whose traced paths cross >= 2 distinct gates (multi-gate
deployment is reported; a lift without multi-gate traces is noise, not
mechanism). n < 40 seeds is an underpowered smoke run and proves
nothing either way.

SEMANTICS PINNED (engineering choices stated plainly)
-----------------------------------------------------
  - get_state_context(lst) -> {0,1,2,3}, total, O(n), priority-ordered:
        0  len(lst) <= 1                  (degenerate / too short)
        1  monotone non-decreasing        (ordered)
        2  max - min <= 15                (compact value range)
        3  otherwise                      (mixed)
    The byte domain (0..255) has no sign, so polarity-style invariants
    are replaced by order/range invariants. Constants GATE_SHORT_LEN=1
    and GATE_RANGE=15 are engineering choices covered by the source sha.
  - The reference input for state tracking is the task's SHORTEST train
    input (deterministic). Runaway intermediate state is defined as []
    (gate 0) from that point on; every primitive is total on [].
  - The plasticity trace fires on STRICT improvement (delta_f > 0), as
    in XVI/XVII; THETA_UP = 2.0 remains the MACRO-ADMISSION threshold.
    (A trace threshold of 2.0 would be unreachable -- fitness lives in
    [-1, 1] -- and would silently disable plasticity.)
  - Budget unit = fitness evaluations, the lineage's accounting unit.
    The gated sampler performs additional O(len) list operations per
    proposed token that flat samplers do not; wall-compute is therefore
    not exactly matched across engines. Recorded as a known accounting
    caveat; within-engine contrasts (GATE5 vs GATE1_5X vs GATED7) are
    unaffected.

GUARDRAILS (permanent; the engine refuses to matter without them)
-----------------------------------------------------------------
    G1  no zero probabilities, anywhere, ever -- across every gate
        slice, including rows/columns added at macro registration
    G2  fitted-manifold entropy does not collapse
    G3  reinforcement is monotone on the (gated) path
    G4  expansion soundness -- macros unpack to primitives only, capped
        at MAX_EXPANDED, behaviour equals expansion behaviour; ladder,
        certify(), difficulty labels live in PRIMITIVE space, untouched
    G5  the gate extractor is total, deterministic, and in-range on
        arbitrary byte lists (fuzzed in the selftest)

CONDITIONS
----------
  COLD       gated 3D engine, empty registry, uniform manifold
  COLD2      identical to COLD; only the PRNG stream label differs
             (THE NOISE FLOOR -- every effect is read against this)
  GATE5      3D gated manifold + macros after 5 recursion rounds
  GATE1_5X   ONE round at 5x per-task source budget: same total source
             compute as GATE5, zero recursion (the control)
  GATED7     like GATE5 but each refit + macro admission must beat the
             incumbent in a counterfactual A/B at equal budget on
             identical streams (atomic accept/reject)
  COMP5      SAME engine, CONSTANT gate (2D + macros) -- Expedition
             XVII's container, re-instantiated for paired contrast
  PLASTIC5   constant gate, registry pinned empty (2D, no macros)
  UNIGRAM5   the Expedition XV static 1D container
  (All chain arms train on the SAME source tasks at the SAME total
   compute; baselines are re-instantiated in this file for pairing and
   are not bit-compatible with the XVI/XVII files.)

KEY CONTRASTS THE REPORT PRINTS
-------------------------------
    GATING LIFT       GATE5  - COMP5     (3D vs 2D, only gate_fn differs)
    MACRO LIFT        COMP5  - PLASTIC5  (XVII's contrast, replicated)
    FULL-STACK SPREAD GATED7 - UNIGRAM5
    RATCHET           GATED7 - GATE5
    RECURSION PREMIUM GATE5  - GATE1_5X  (compute-matched)
    ... plus LEVEL-4-only versions and deployment descriptives
    (registry size, macro-solves, multi-gate-solves, expanded depth).

USAGE
-----
    python3 leapforge_gated.py audit
    python3 leapforge_gated.py test
    python3 leapforge_gated.py build
    python3 leapforge_gated.py battery --seeds 1-6 [--profile smoke]
    python3 leapforge_gated.py report  [--profile smoke]
    python3 leapforge_gated.py replay  [--profile smoke]
    python3 leapforge_gated.py sample 4

HARD RULES
----------
  - Do not edit this file before replaying existing ledgers: GENESIS
    embeds the source sha; replay doubles as code-identity proof.
  - One unit per (config, condition, seed); reruns are refused.
  - No random / numpy / time inside the engine (AST-audited). All
    randomness flows through SHA-256-seeded XorShift64Star streams.
  - PRIMS, enumeration, and certify() are axioms carried verbatim from
    Expeditions XIV-XVII; the token/gate layers never write into them.
  - Improvements go in a NEW file with the same audit + test + replay
    discipline, recording what changed and why.
"""

import ast
import hashlib
import json
import math
import os
import sys

VERSION = "gated-xviii-1.0"
LINE_CAP = 2300
MAXLEN = 24
MAX_DEPTH = 4          # program length cap in TOKENS
MAX_EXPANDED = 10      # program length cap in PRIMITIVES after expansion
MAX_MACROS = 6
MACRO_MIN = 2
MACRO_MAX = 3
THETA_UP = 2.0         # macro-admission cumulative-weight threshold
MIN_SUPPORT = 2
GATE_SHORT_LEN = 1     # gate 0: len <= this
GATE_RANGE = 15        # gate 2: max - min <= this
NUM_GATES = 4

CONFIG_FULL = {
    "version": VERSION,
    "profile": "full",
    "n_rounds": 5,
    "src_budget": 2500,
    "eval_budget": 4000,
    "gate_budget": 800,
    "n_probe": 3,
    "src_levels": [2, 2, 3, 3, 3],
    "eval_levels": [[3, 6], [4, 6]],
    "pop_size": 32,
    "pool_keep": 24,
    "eta": 0.5,
    "lambda": 0.90,
    "outdir": "runs",
}

CONFIG_SMOKE = {
    "version": VERSION,
    "profile": "smoke",
    "n_rounds": 5,
    "src_budget": 800,
    "eval_budget": 1400,
    "gate_budget": 350,
    "n_probe": 2,
    "src_levels": [2, 3, 3],
    "eval_levels": [[3, 4], [4, 4]],
    "pop_size": 24,
    "pool_keep": 24,
    "eta": 0.5,
    "lambda": 0.90,
    "outdir": "runs",
}

CONFIG = dict(CONFIG_FULL)

CONDS = ["COLD", "COLD2", "GATE5", "GATE1_5X", "GATED7",
         "COMP5", "PLASTIC5", "UNIGRAM5"]

PREREG = ("Prediction written before any run: GATING LIFT GATE5 - COMP5 "
          "sits inside the noise floor -- container richness dies a third "
          "time (after Exp VII n-grams and the XVI/XVII smoke directions), "
          "recorded as the finding. The live alternative requires BOTH "
          "GATE5 - COMP5 above the floor AND solved frontier tasks whose "
          "traced paths cross >= 2 distinct gates. A lift without "
          "multi-gate deployment is noise, not mechanism. n < 40 seeds "
          "proves nothing either way.")


# ---------------------------------------------------------------------------
# DETERMINISM -- one PRNG, text-seeded (identical to XV/XVI/XVII).
# ---------------------------------------------------------------------------

_MASK = (1 << 64) - 1


class XorShift64Star(object):
    def __init__(self, seed_text):
        d = hashlib.sha256(str(seed_text).encode("utf-8")).digest()
        self.state = int.from_bytes(d[:8], "big") or 0x9E3779B97F4A7C15

    def u64(self):
        x = self.state
        x ^= x >> 12
        x ^= (x << 25) & _MASK
        x ^= x >> 27
        self.state = x
        return (x * 2685821657736338717) & _MASK

    def below(self, n):
        return self.u64() % n if n > 0 else 0

    def unit(self):
        return self.u64() / float(1 << 64)

    def choice(self, seq):
        return seq[self.below(len(seq))]


# ---------------------------------------------------------------------------
# SOURCE AUDIT -- forbidden imports, no dynamic eval, line cap, banned claims.
# ---------------------------------------------------------------------------

FORBIDDEN_MODULES = {"random", "secrets", "numpy", "torch", "time", "pickle",
                     "multiprocessing", "threading", "socket", "subprocess"}


def _self_source():
    with open(os.path.abspath(__file__), "r", encoding="utf-8") as f:
        return f.read()


def _banned_words():
    # stored reversed so this file cannot trip its own detector
    rev = ["iga", "isa", "tnegreme", "ecnegreme", "ecnegilletnirepus",
           "ytiralugnis", "dednuobnu", "tneitnes", "suoicsnoc",
           "ssensuoicsnoc"]
    return [w[::-1] for w in rev]


def _source_tokens(src):
    return set("".join(c if (c.isalnum() or c == "_") else " "
                       for c in src.lower()).split())


def audit_sources(quiet=False):
    src = _self_source()
    lines = src.count("\n") + 1
    tree = ast.parse(src)
    mods, dyn = set(), []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in ("eval", "exec"):
            dyn.append(node.func.id)
    bad = mods & FORBIDDEN_MODULES
    if bad:
        sys.exit("AUDIT FAIL (forbidden imports): %s" % sorted(bad))
    if dyn:
        sys.exit("AUDIT FAIL (dynamic eval): %s" % dyn)
    if lines > LINE_CAP:
        sys.exit("AUDIT FAIL (line cap): %d > %d" % (lines, LINE_CAP))
    toks = _source_tokens(src)
    hit = [w for w in _banned_words() if w in toks]
    if hit:
        sys.exit("AUDIT FAIL (banned claim words): %s" % hit)
    sha = hashlib.sha256(src.encode("utf-8")).hexdigest()
    rep = {"lines": lines, "imports": sorted(mods), "source_sha": sha}
    if not quiet:
        print("AUDIT PASS  lines=%d  imports=%s" % (lines, sorted(mods)))
        print("source sha256 = %s" % sha)
    return rep


# ---------------------------------------------------------------------------
# LEDGER -- append-only, hash-chained (identical contract to XV/XVI/XVII).
# ---------------------------------------------------------------------------

GENESIS_PREV = "0" * 64


def canon(body):
    return json.dumps(body, sort_keys=True, separators=(",", ":"))


def record_hash(prev_hash, body):
    return hashlib.sha256((prev_hash + canon(body)).encode()).hexdigest()


class Ledger(object):
    def __init__(self, path):
        self.path = path                     # path=None -> in-memory only
        self.records = []
        self.prev = GENESIS_PREV
        if path is not None and os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        self.records.append(json.loads(line))
            self.verify()
            if self.records:
                self.prev = self.records[-1]["hash"]

    def verify(self):
        prev = GENESIS_PREV
        for i, rec in enumerate(self.records):
            if rec["prev"] != prev:
                sys.exit("LEDGER BROKEN at record %d (prev mismatch)" % i)
            if record_hash(prev, rec["body"]) != rec["hash"]:
                sys.exit("LEDGER BROKEN at record %d (hash mismatch)" % i)
            prev = rec["hash"]
        return True

    def append(self, kind, body):
        rec = {"kind": kind, "body": body, "prev": self.prev,
               "hash": record_hash(self.prev, body)}
        self.records.append(rec)
        if self.path is not None:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(canon(rec) + "\n")
        self.prev = rec["hash"]
        return rec["hash"]

    def find(self, kind, **match):
        out = []
        for rec in self.records:
            if rec["kind"] != kind:
                continue
            if all(rec["body"].get(k) == v for k, v in match.items()):
                out.append(rec)
        return out


# ---------------------------------------------------------------------------
# SUBSTRATE -- Expedition XIV pipeline DSL, carried VERBATIM (axiom).
# ---------------------------------------------------------------------------

def _c(x):
    return [v & 0xFF for v in x][:MAXLEN]


PRIMS = {
    "inc":      lambda x: _c([v + 1 for v in x]),
    "dec":      lambda x: _c([v - 1 for v in x]),
    "double":   lambda x: _c([v * 2 for v in x]),
    "half":     lambda x: _c([v // 2 for v in x]),
    "neg":      lambda x: _c([255 - v for v in x]),
    "add5":     lambda x: _c([v + 5 for v in x]),
    "mod10":    lambda x: _c([v % 10 for v in x]),
    "reverse":  lambda x: _c(list(reversed(x))),
    "sort":     lambda x: _c(sorted(x)),
    "rotate":   lambda x: _c(x[1:] + x[:1] if x else []),
    "dedupe":   lambda x: _c([v for i, v in enumerate(x)
                              if i == 0 or v != x[i - 1]]),
    "evens":    lambda x: _c([v for v in x if v % 2 == 0]),
    "big":      lambda x: _c([v for v in x if v > 128]),
    "tail":     lambda x: _c(x[1:]),
    "init":     lambda x: _c(x[:-1]),
    "cumsum":   lambda x: _c([sum(x[:i + 1]) for i in range(len(x))]),
    "cummax":   lambda x: _c([max(x[:i + 1]) for i in range(len(x))]),
    "diff":     lambda x: _c([x[i] - (x[i - 1] if i else 0)
                              for i in range(len(x))]),
    "dup":      lambda x: _c([v for v in x for _ in range(2)]),
    "pairsum":  lambda x: _c([x[i] + x[i + 1] for i in range(len(x) - 1)]),
}
NAMES = sorted(PRIMS)

PROBES = [
    [3, 1, 4, 1, 5, 9],
    [200, 7, 7, 90],
    [0, 255, 128, 64],
    [10, 20, 30, 40, 50],
    [9, 9, 2],
    [2, 2, 2, 2],
    [17, 4, 200, 3, 3, 88],
]


def run(pipe, xs):
    v = list(xs)
    for name in pipe:
        v = PRIMS[name](v)
        if len(v) > MAXLEN:
            return None
    return v


def sig(pipe):
    out = []
    for xs in PROBES:
        o = run(pipe, xs)
        if o is None:
            return None
        out.append(tuple(o))
    return tuple(out)


IDENT = sig([])


def substrate_fingerprint():
    table = {nm: sig([nm]) for nm in NAMES}
    return hashlib.sha256(
        canon({"probes": PROBES, "prims": {k: list(map(list, v)) if v else
                                           None for k, v in table.items()}})
        .encode()).hexdigest()[:16]


def build(max_depth=MAX_DEPTH, verbose=False):
    seen = {IDENT: (0, [])}
    frontier = [[]]
    levels = {}
    for d in range(1, max_depth + 1):
        nxt, new, cand = [], [], 0
        for p in frontier:
            for nm in NAMES:
                q = p + [nm]
                cand += 1
                s = sig(q)
                if s is None or s in seen:
                    continue
                seen[s] = (d, q)
                new.append((s, q))
                nxt.append(q)
        frontier = nxt
        levels[d] = new
        if verbose:
            print("  depth %d: %6d candidates -> %6d new behaviours "
                  "(%6d cumulative)" % (d, cand, len(new), len(seen)))
        if not frontier:
            break
    return seen, levels


_LADDER = [None]


def _cache_path():
    return os.path.join(CONFIG["outdir"], "ladder_cache.json")


def get_ladder():
    if _LADDER[0] is not None:
        return _LADDER[0]
    fp = substrate_fingerprint()
    cp = _cache_path()
    if os.path.exists(cp):
        try:
            with open(cp, "r", encoding="utf-8") as f:
                c = json.load(f)
            body = c.get("levels", {})
            if (c.get("fingerprint") == fp
                    and c.get("max_depth") == MAX_DEPTH
                    and hashlib.sha256(canon(body).encode()).hexdigest()
                    == c.get("sha")):
                levels = {int(d): [(None, p) for p in body[d]]
                          for d in body}
                _LADDER[0] = (None, levels)
                return _LADDER[0]
        except (ValueError, KeyError, OSError):
            pass
    print("(building ladder: enumerating all pipelines to depth %d...)"
          % MAX_DEPTH)
    seen, levels = build(MAX_DEPTH, verbose=True)
    body = {str(d): [p for _s, p in levels[d]] for d in sorted(levels)}
    c = {"fingerprint": fp, "max_depth": MAX_DEPTH, "levels": body,
         "sha": hashlib.sha256(canon(body).encode()).hexdigest()}
    if not os.path.isdir(CONFIG["outdir"]):
        os.makedirs(CONFIG["outdir"])
    with open(cp, "w", encoding="utf-8") as f:
        f.write(canon(c))
    _LADDER[0] = (seen, levels)
    return _LADDER[0]


def make_task(pipe, prng, n_train=4, n_test=4):
    def mk(lo, hi, n):
        out = []
        for _ in range(n):
            length = lo + prng.below(hi - lo + 1)
            out.append([prng.below(256) for _ in range(length)])
        return out
    tr_in, te_in = mk(3, 6, n_train), mk(7, 11, n_test)
    tr = [(x, run(pipe, x)) for x in tr_in]
    te = [(x, run(pipe, x)) for x in te_in]
    if any(o is None for _x, o in tr + te):
        return None
    if all(len(o) == 0 for _x, o in tr):
        return None
    if all(o == x for x, o in tr):
        return None
    return {"train": tr, "test": te, "pipe": list(pipe), "level": len(pipe)}


def certify(task, level):
    _seen, levels = get_ladder()
    for d in range(1, level):
        for _s, pipe in levels.get(d, []):
            if all(run(pipe, x) == y for x, y in task["train"]):
                return False
    return True


def pool_split(level, seed):
    _seen, levels = get_ladder()
    n = len(levels.get(level, []))
    idx = list(range(n))
    prng = XorShift64Star("split|%d|%s" % (level, seed))
    for i in range(n - 1, 0, -1):
        j = prng.below(i + 1)
        idx[i], idx[j] = idx[j], idx[i]
    half = n // 2
    return idx[:half], idx[half:]


def draw_task(level, seed, kind, tag, max_tries=400):
    _seen, levels = get_ladder()
    pool = levels.get(level, [])
    src_idx, tgt_idx = pool_split(level, seed)
    ids = src_idx if kind == "source" else tgt_idx
    prng = XorShift64Star("draw|%s|%d|%s|%s" % (kind, level, seed, tag))
    for _ in range(max_tries):
        _s, pipe = pool[ids[prng.below(len(ids))]]
        t = make_task(pipe, prng)
        if t is None:
            continue
        if not certify(t, level):
            continue
        return t
    sys.exit("draw_task exhausted (level %d, %s, %s)" % (level, kind, tag))


# ---------------------------------------------------------------------------
# STATE-CONTEXT GATES (G5) + MACRO REGISTRY + VIRTUAL RUNTIME (G4).
# ---------------------------------------------------------------------------

def get_state_context(lst):
    """Coarse discrete invariant of a list state. Total, deterministic,
    O(n), priority-ordered. Returns an int in [0, NUM_GATES)."""
    n = len(lst)
    if n <= GATE_SHORT_LEN:
        return 0
    mono = True
    i = 1
    while i < n:
        if lst[i] < lst[i - 1]:
            mono = False
            break
        i += 1
    if mono:
        return 1
    lo = lst[0]
    hi = lst[0]
    for v in lst:
        if v < lo:
            lo = v
        if v > hi:
            hi = v
    if hi - lo <= GATE_RANGE:
        return 2
    return 3


def gate_const(_lst):
    """Constant gate: collapses the 3D manifold to one slice (the 2D
    baseline engine, machinery otherwise identical)."""
    return 0


def gate_keys_for(gate_fn):
    if gate_fn is gate_const:
        return ["g0"]
    return ["g%d" % i for i in range(NUM_GATES)]


def token_space(reg):
    return NAMES + sorted(reg)


def expand_tokens(tokens, reg):
    out = []
    for t in tokens:
        if t in reg:
            for nm in reg[t]:
                out.append(nm)
        else:
            out.append(t)
        if len(out) > MAX_EXPANDED:
            return None
    return out


def run_tokens(tokens, reg, xs):
    exp = expand_tokens(tokens, reg)
    if exp is None:
        return None
    return run(exp, xs)


def apply_token(v, tok, reg):
    """Advance the tracked list state by one token. Runaway or overlong
    intermediate state collapses to [] (gate 0), a defined total value."""
    if v is None:
        return []
    out = list(v)
    body = reg[tok] if tok in reg else [tok]
    for nm in body:
        out = PRIMS[nm](out)
        if len(out) > MAXLEN:
            return []
    return out


def _start_key(depth):
    d = depth if depth >= 1 else 1
    d = MAX_DEPTH if d > MAX_DEPTH else d
    return "<S%d>" % d


def start_rows():
    return [_start_key(d) for d in range(1, MAX_DEPTH + 1)]


def manifold_rows(reg):
    return token_space(reg) + start_rows()


def uniform_manifold(reg, gate_fn):
    toks = token_space(reg)
    rows = manifold_rows(reg)
    return {gk: {r: {c: 1.0 for c in toks} for r in rows}
            for gk in gate_keys_for(gate_fn)}


def copy_manifold(W):
    return {gk: {r: dict(W[gk][r]) for r in W[gk]} for gk in W}


def grow_manifold(W, reg):
    """Dynamic expansion at macro registration: every gate slice gets a
    floor-weight column in every row and a floor-weight row per new
    token (G1 by construction); learned weights are preserved."""
    toks = token_space(reg)
    rows = manifold_rows(reg)
    out = {}
    for gk in W:
        slice_old = W[gk]
        slice_new = {}
        for r in rows:
            old = slice_old.get(r, {})
            row = {}
            for c in toks:
                row[c] = old[c] if c in old else 1.0
            slice_new[r] = row
        out[gk] = slice_new
    return out


def gated_transitions(pipe, reg, ref, gate_fn):
    """The active manifold cross-section of a program on a reference
    input: [(gate_key, prev_row, next_token), ...]. The start edge is
    keyed by the program's token depth; the gate is the state invariant
    BEFORE the token executes."""
    if not pipe:
        return []
    out = []
    v = list(ref)
    prev = _start_key(len(pipe))
    for tok in pipe:
        gk = "g%d" % gate_fn(v)
        out.append((gk, prev, tok))
        v = apply_token(v, tok, reg)
        prev = tok
    return out


def fit_manifold(scored, reg, gate_fn, keep=None, strength=3.0):
    """Floor 1.0 on every edge of every gate slice (G1), plus
    strength * fitness per traversed (gate, prev, next) edge over the
    top-`keep` harvested programs, each traced on its OWN task's
    reference input."""
    keep = keep or CONFIG["pool_keep"]
    W = uniform_manifold(reg, gate_fn)
    toks = set(token_space(reg))
    for f, prog, ref in sorted(scored, key=lambda t: (-t[0], t[1]))[:keep]:
        if f <= 0.0:
            continue
        bad = False
        for t in prog:
            if t not in toks:
                bad = True
                break
        if bad:
            continue
        for gk, a, b in gated_transitions(prog, reg, ref, gate_fn):
            W[gk][a][b] = W[gk][a][b] + strength * f
    return W


def _round_obj(o):
    if isinstance(o, dict):
        return {k: _round_obj(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_round_obj(v) for v in o]
    if isinstance(o, float):
        return round(o, 9)
    return o


def prior_sha(obj):
    return hashlib.sha256(canon(_round_obj(obj)).encode()).hexdigest()[:16]


def pack_prior(W, reg):
    return {"W": W, "reg": {k: list(v) for k, v in sorted(reg.items())}}


def manifold_min(W):
    m = None
    for gk in W:
        for r in W[gk]:
            for v in W[gk][r].values():
                if m is None or v < m:
                    m = v
    return m


def manifold_row_entropy(W):
    hs = []
    for gk in W:
        for r in W[gk]:
            tot = sum(W[gk][r].values())
            h = 0.0
            for v in W[gk][r].values():
                p = v / tot
                if p > 0.0:
                    h -= p * math.log2(p)
            hs.append(h)
    return sum(hs) / len(hs)


def mine_macros(scored, reg):
    """Identical admission rule to Expedition XVII: cumulative fitness
    weight >= THETA_UP over >= MIN_SUPPORT distinct programs; bodies are
    primitive-only windows of length MACRO_MIN..MACRO_MAX; capped."""
    stats = {}
    top = sorted(scored, key=lambda t: (-t[0], t[1]))[:CONFIG["pool_keep"]]
    for pid, entry in enumerate(top):
        f, prog = entry[0], entry[1]
        if f <= 0.0:
            continue
        exp = expand_tokens(prog, reg)
        if exp is None:
            continue
        for w in range(MACRO_MIN, MACRO_MAX + 1):
            for i in range(0, len(exp) - w + 1):
                seq = tuple(exp[i:i + w])
                if seq not in stats:
                    stats[seq] = {"w": 0.0, "progs": set()}
                stats[seq]["w"] += f
                stats[seq]["progs"].add(pid)
    existing = {tuple(v) for v in reg.values()}
    ranked = sorted(stats.items(),
                    key=lambda kv: (-kv[1]["w"], -len(kv[0]), kv[0]))
    new_names = []
    nxt = len(reg) + 1
    for seq, st in ranked:
        if len(reg) >= MAX_MACROS:
            break
        if st["w"] < THETA_UP or len(st["progs"]) < MIN_SUPPORT:
            continue
        if seq in existing:
            continue
        ok = True
        for nm in seq:
            if nm not in PRIMS:
                ok = False
                break
        if not ok:
            continue
        name = "m%02d" % nxt
        nxt += 1
        reg[name] = list(seq)
        existing.add(seq)
        new_names.append(name)
    return reg, new_names


# ---------------------------------------------------------------------------
# SEARCH -- population EA over TOKEN pipelines; the sampling walk tracks
# the list state on a reference input and draws from the active gate
# slice. ONE engine; the 2D baseline is gate_const.
# ---------------------------------------------------------------------------

def sample_next(gk, prev, W, toks, prng):
    row = W[gk][prev]
    total = 0.0
    for nm in toks:
        total += row[nm]
    r = prng.unit() * total
    acc = 0.0
    for nm in toks:
        acc += row[nm]
        if r <= acc:
            return nm
    return toks[-1]


def random_pipe(W, reg, toks, ref, gate_fn, prng):
    depth = 1 + prng.below(MAX_DEPTH)
    out = []
    v = list(ref)
    prev = _start_key(depth)
    for _ in range(depth):
        gk = "g%d" % gate_fn(v)
        nm = sample_next(gk, prev, W, toks, prng)
        out.append(nm)
        v = apply_token(v, nm, reg)
        prev = nm
    return out


def _state_at(pipe, k, reg, ref):
    v = list(ref)
    for i in range(k):
        v = apply_token(v, pipe[i], reg)
    return v


def mutate_pipe(pipe, W, reg, toks, ref, gate_fn, prng):
    p = list(pipe)
    for _ in range(1 + prng.below(2)):
        r = prng.unit()
        if r < 0.35 and len(p) < MAX_DEPTH:
            k = prng.below(len(p) + 1)
            prev = p[k - 1] if k > 0 else _start_key(len(p) + 1)
            gk = "g%d" % gate_fn(_state_at(p, k, reg, ref))
            p.insert(k, sample_next(gk, prev, W, toks, prng))
        elif r < 0.65 and len(p) > 1:
            p.pop(prng.below(len(p)))
        elif p:
            k = prng.below(len(p))
            prev = p[k - 1] if k > 0 else _start_key(len(p))
            gk = "g%d" % gate_fn(_state_at(p, k, reg, ref))
            p[k] = sample_next(gk, prev, W, toks, prng)
    if not p:
        gk = "g%d" % gate_fn(list(ref))
        p = [sample_next(gk, _start_key(1), W, toks, prng)]
    return p


def crossover(p1, p2, prng):
    c = p1[:prng.below(len(p1) + 1)] + p2[prng.below(len(p2) + 1):]
    c = c[:MAX_DEPTH]
    return c if c else list(p1[:1] or p2[:1])


def check_exact_tokens(pipe, reg, examples):
    for x, y in examples:
        if run_tokens(pipe, reg, x) != y:
            return False
    return True


def fitness_tokens(pipe, reg, examples):
    tot = 0.0
    for x, y in examples:
        out = run_tokens(pipe, reg, x)
        if out is None:
            return -1.0
        if out == y:
            tot += 1.0
            continue
        denom = max(len(y), len(out), 1)
        m = sum(1 for a, b in zip(out, y) if a == b)
        tot += 0.85 * (m / float(denom)) + (0.1 if len(out) == len(y) else 0.0)
    return tot / len(examples)


def _tournament(pop, prng, k=3):
    best = pop[prng.below(len(pop))]
    for _ in range(k - 1):
        c = pop[prng.below(len(pop))]
        if c[0] > best[0]:
            best = c
    return best


def _decay_toward(W_loc, W_base, lam):
    for gk in W_loc:
        for r in W_loc[gk]:
            loc_r, base_r = W_loc[gk][r], W_base[gk][r]
            for c in loc_r:
                loc_r[c] = lam * loc_r[c] + (1.0 - lam) * base_r[c]


def _reinforce(W_loc, trips, amount):
    for gk, a, b in trips:
        W_loc[gk][a][b] = W_loc[gk][a][b] + amount


def search_task_gated(task, W_base, reg, budget, prng, gate_fn):
    """Population EA over token pipelines with a state-gated local
    manifold. Plasticity: on strict improvement of the running best
    partial fitness, the ACTIVE cross-section (gate, prev, next) of the
    improving program -- traced on the reference input -- receives
    eta * delta_f * xi; the local manifold decays toward base each
    generation. Returns (program|None, evals_used, elite_pool)."""
    ps = CONFIG["pop_size"]
    eta = CONFIG["eta"]
    lam = CONFIG["lambda"]
    xi = float(task["level"]) / float(MAX_DEPTH)
    toks = token_space(reg)
    guide = sorted(task["train"], key=lambda e: len(e[0]))[:2]
    ref = guide[0][0]
    W_loc = copy_manifold(W_base)
    evals = [0]
    best_f = [0.0]

    def ev(p):
        evals[0] += 1
        f = fitness_tokens(p, reg, guide)
        if eta > 0.0 and f > best_f[0]:
            trips = gated_transitions(p, reg, ref, gate_fn)
            _reinforce(W_loc, trips, eta * (f - best_f[0]) * xi)
        if f > best_f[0]:
            best_f[0] = f
        return f

    pop = []
    while len(pop) < ps and evals[0] < budget:
        p = random_pipe(W_loc, reg, toks, ref, gate_fn, prng)
        f = ev(p)
        if f >= 1.0 and check_exact_tokens(p, reg, task["train"]):
            return p, evals[0], [(f, p)]
        pop.append((f, p))
    while evals[0] < budget:
        _decay_toward(W_loc, W_base, lam)
        pop.sort(key=lambda t: -t[0])
        elite = pop[:max(2, ps // 4)]
        newpop = list(elite)
        while len(newpop) < ps and evals[0] < budget:
            r = prng.unit()
            if r < 0.30:
                c = random_pipe(W_loc, reg, toks, ref, gate_fn, prng)
            elif r < 0.65:
                c = mutate_pipe(_tournament(pop, prng)[1], W_loc, reg,
                                toks, ref, gate_fn, prng)
            else:
                c = crossover(_tournament(pop, prng)[1],
                              _tournament(pop, prng)[1], prng)
            f = ev(c)
            if f >= 1.0 and check_exact_tokens(c, reg, task["train"]):
                return c, evals[0], [(f2, p2) for f2, p2 in elite[:12]]
            newpop.append((f, c))
        pop = newpop
    pop.sort(key=lambda t: -t[0])
    return None, evals[0], [(f, p) for f, p in pop[:12]]


# ---------------------------------------------------------------------------
# THE 1D BASELINE ENGINE -- Expedition XV's container, ported verbatim.
# ---------------------------------------------------------------------------

def uniform_prior_u():
    return {nm: 1.0 for nm in NAMES}


def fit_prior_u(scored, keep=None, strength=3.0):
    keep = keep or CONFIG["pool_keep"]
    w = uniform_prior_u()
    for entry in sorted(scored, key=lambda t: (-t[0], t[1]))[:keep]:
        f, prog = entry[0], entry[1]
        if f <= 0.0:
            continue
        for nm in prog:
            w[nm] = w.get(nm, 1.0) + strength * f
    return w


def sample_name_u(w, prng):
    total = sum(w[nm] for nm in NAMES)
    r = prng.unit() * total
    acc = 0.0
    for nm in NAMES:
        acc += w[nm]
        if r <= acc:
            return nm
    return NAMES[-1]


def random_pipe_u(w, prng):
    depth = 1 + prng.below(MAX_DEPTH)
    return [sample_name_u(w, prng) for _ in range(depth)]


def mutate_u(pipe, w, prng):
    p = list(pipe)
    for _ in range(1 + prng.below(2)):
        r = prng.unit()
        if r < 0.35 and len(p) < MAX_DEPTH:
            p.insert(prng.below(len(p) + 1), sample_name_u(w, prng))
        elif r < 0.65 and len(p) > 1:
            p.pop(prng.below(len(p)))
        elif p:
            p[prng.below(len(p))] = sample_name_u(w, prng)
    return p if p else [sample_name_u(w, prng)]


def fitness_u(pipe, examples):
    tot = 0.0
    for x, y in examples:
        out = run(pipe, x)
        if out is None:
            return -1.0
        if out == y:
            tot += 1.0
            continue
        denom = max(len(y), len(out), 1)
        m = sum(1 for a, b in zip(out, y) if a == b)
        tot += 0.85 * (m / float(denom)) + (0.1 if len(out) == len(y) else 0.0)
    return tot / len(examples)


def search_task_u(task, w, budget, prng):
    ps = CONFIG["pop_size"]
    guide = sorted(task["train"], key=lambda e: len(e[0]))[:2]
    evals = [0]

    def ev(p):
        evals[0] += 1
        return fitness_u(p, guide)

    def full(p):
        return all(run(p, x) == y for x, y in task["train"])

    pop = []
    while len(pop) < ps and evals[0] < budget:
        p = random_pipe_u(w, prng)
        f = ev(p)
        if f >= 1.0 and full(p):
            return p, evals[0], [(f, p)]
        pop.append((f, p))
    while evals[0] < budget:
        pop.sort(key=lambda t: -t[0])
        elite = pop[:max(2, ps // 4)]
        newpop = list(elite)
        while len(newpop) < ps and evals[0] < budget:
            r = prng.unit()
            if r < 0.30:
                c = random_pipe_u(w, prng)
            elif r < 0.65:
                c = mutate_u(_tournament(pop, prng)[1], w, prng)
            else:
                c = crossover(_tournament(pop, prng)[1],
                              _tournament(pop, prng)[1], prng)
            f = ev(c)
            if f >= 1.0 and full(c):
                return c, evals[0], [(f2, p2) for f2, p2 in elite[:12]]
            newpop.append((f, c))
        pop = newpop
    pop.sort(key=lambda t: -t[0])
    return None, evals[0], [(f, p) for f, p in pop[:12]]


def solves_tokens(pipe, reg, task):
    return (pipe is not None
            and check_exact_tokens(pipe, reg, task["train"])
            and check_exact_tokens(pipe, reg, task["test"]))


def solves_u(pipe, task):
    return (pipe is not None
            and all(run(pipe, x) == y for x, y in task["train"])
            and all(run(pipe, x) == y for x, y in task["test"]))


# ---------------------------------------------------------------------------
# THE COUNTERFACTUAL GATE -- equal budget, identical PRNG streams.
# ---------------------------------------------------------------------------

def trial_gated(W, reg, probe_tasks, budget, seed_text, gate_fn):
    solved, cost = 0, 0
    for i, t in enumerate(probe_tasks):
        prng = XorShift64Star("%s|%d" % (seed_text, i))
        prog, c, _e = search_task_gated(t, W, reg, budget, prng, gate_fn)
        cost += c
        if solves_tokens(prog, reg, t):
            solved += 1
    return solved, cost


def gate_ab(inc_W, inc_reg, cand_W, cand_reg, probe_tasks, budget,
            seed_text, gate_fn):
    inc_s, inc_c = trial_gated(inc_W, inc_reg, probe_tasks, budget,
                               seed_text, gate_fn)
    can_s, can_c = trial_gated(cand_W, cand_reg, probe_tasks, budget,
                               seed_text, gate_fn)
    accept = (can_s > inc_s) or (can_s == inc_s and can_c < inc_c * 0.95)
    return accept, {"inc_solved": inc_s, "cand_solved": can_s,
                    "inc_cost": inc_c, "cand_cost": can_c,
                    "accepted": bool(accept)}


# ---------------------------------------------------------------------------
# CHAINS -- six arms, all trained on the SAME source tasks at the SAME
# total compute: gated 3D (plain / 5x / ratchet-gated), 2D + macros,
# 2D no-macros, 1D static.
# ---------------------------------------------------------------------------

def _harvest(pool, prog, elite, ref):
    if prog is not None:
        pool.append((1.0, list(prog), list(ref)))
    for f, p in elite[:3]:
        if f > 0.0:
            pool.append((f, list(p), list(ref)))


def _run_arm(seed, tag_solve, gate_fn, with_macros, rounds, budget_each):
    """One training arm: `rounds` rounds over the source levels; harvest,
    optionally mine macros, refit. Returns (W, reg, evals, snapshots)."""
    cfg = CONFIG
    pool = []
    reg = {}
    W = uniform_manifold(reg, gate_fn)
    used = 0
    snaps = []
    for rnd in range(1, rounds + 1):
        for i, lvl in enumerate(cfg["src_levels"]):
            t = draw_task(lvl, seed, "source", "src|%d|%d" % (rnd, i))
            ref = sorted(t["train"], key=lambda e: len(e[0]))[0][0]
            prog, ev_, elite = search_task_gated(
                t, W, reg, budget_each,
                XorShift64Star("%s|%s|%d|%d" % (tag_solve, seed, rnd, i)),
                gate_fn)
            used += ev_
            _harvest(pool, prog, elite, ref)
        if with_macros:
            reg, _new = mine_macros(pool, dict(reg))
        W = fit_manifold(pool, reg, gate_fn)
        snaps.append({"W": copy_manifold(W),
                      "reg": {k: list(v) for k, v in reg.items()}})
    return W, reg, used, snaps


def build_chains(seed):
    cfg = CONFIG
    fp0 = substrate_fingerprint()
    n_src = len(cfg["src_levels"])
    budget_arm = cfg["n_rounds"] * n_src * cfg["src_budget"]

    # --- gated 3D chain (macros + state gates) ---
    gW, greg, g_evals, _gs = _run_arm(seed, "solve", get_state_context,
                                      True, cfg["n_rounds"],
                                      cfg["src_budget"])
    gate5 = {"W": gW, "reg": greg}
    if substrate_fingerprint() != fp0:
        sys.exit("SUBSTRATE FINGERPRINT DRIFT -- aborting")

    # --- compute-matched one-shot (3D engine, one round at 5x) ---
    xW, xreg, x_evals, _xs = _run_arm(seed, "solve5x", get_state_context,
                                      True, 1,
                                      cfg["src_budget"] * cfg["n_rounds"])
    five_x = {"W": xW, "reg": xreg}

    # --- ratchet-gated 3D chain: refit + macros as ONE atomic proposal ---
    gpool, glog = [], []
    inc_reg = {}
    inc_W = uniform_manifold(inc_reg, get_state_context)
    g7_evals = 0
    for rnd in range(1, cfg["n_rounds"] + 1):
        for i, lvl in enumerate(cfg["src_levels"]):
            t = draw_task(lvl, seed, "source", "gsrc|%d|%d" % (rnd, i))
            ref = sorted(t["train"], key=lambda e: len(e[0]))[0][0]
            prog, ev_, elite = search_task_gated(
                t, inc_W, inc_reg, cfg["src_budget"],
                XorShift64Star("g7solve|%s|%d|%d" % (seed, rnd, i)),
                get_state_context)
            g7_evals += ev_
            _harvest(gpool, prog, elite, ref)
        cand_reg, cand_new = mine_macros(gpool, dict(inc_reg))
        cand_W = fit_manifold(gpool, cand_reg, get_state_context)
        probes = [draw_task(3, seed, "source", "probe|%d|%d" % (rnd, j))
                  for j in range(cfg["n_probe"])]
        acc, info = gate_ab(inc_W, inc_reg, cand_W, cand_reg, probes,
                            cfg["gate_budget"],
                            "gate7|%s|%d" % (seed, rnd), get_state_context)
        info["round"] = rnd
        info["cand_new_macros"] = list(cand_new)
        glog.append(info)
        if acc:
            inc_W, inc_reg = cand_W, cand_reg
        if substrate_fingerprint() != fp0:
            sys.exit("SUBSTRATE FINGERPRINT DRIFT -- aborting")
    gated7 = {"W": inc_W, "reg": inc_reg}

    # --- 2D + macros baseline (constant gate; XVII's container) ---
    cW, creg, c_evals, _cs = _run_arm(seed, "csolve", gate_const,
                                      True, cfg["n_rounds"],
                                      cfg["src_budget"])
    comp5 = {"W": cW, "reg": creg}

    # --- 2D no-macros baseline ---
    pW, _preg, p_evals, _ps = _run_arm(seed, "psolve", gate_const,
                                       False, cfg["n_rounds"],
                                       cfg["src_budget"])
    plastic5 = {"W": pW, "reg": {}}

    # --- 1D static baseline ---
    upool, wu = [], uniform_prior_u()
    u_evals = 0
    for rnd in range(1, cfg["n_rounds"] + 1):
        for i, lvl in enumerate(cfg["src_levels"]):
            t = draw_task(lvl, seed, "source", "src|%d|%d" % (rnd, i))
            prog, ev_, elite = search_task_u(
                t, wu, cfg["src_budget"],
                XorShift64Star("usolve|%s|%d|%d" % (seed, rnd, i)))
            u_evals += ev_
            ref = sorted(t["train"], key=lambda e: len(e[0]))[0][0]
            _harvest(upool, prog, elite, ref)
        wu = fit_prior_u(upool)
    unigram5 = dict(wu)

    for used, name in ((g_evals, "gate3d"), (x_evals, "5x"),
                       (g7_evals, "gated7"), (c_evals, "comp2d"),
                       (p_evals, "plastic2d"), (u_evals, "unigram")):
        assert used <= budget_arm, "I0 budget violated in %s arm" % name
    assert budget_arm == n_src * (cfg["src_budget"] * cfg["n_rounds"]), \
        "compute-match broken by config"

    meta = {
        "seed": seed,
        "fingerprint": fp0,
        "gate5_sha": prior_sha(pack_prior(gate5["W"], gate5["reg"])),
        "gate5_macros": sorted(gate5["reg"]),
        "five_x_sha": prior_sha(pack_prior(five_x["W"], five_x["reg"])),
        "gated7_sha": prior_sha(pack_prior(gated7["W"], gated7["reg"])),
        "gated7_macros": sorted(gated7["reg"]),
        "comp5_sha": prior_sha(pack_prior(comp5["W"], comp5["reg"])),
        "plastic5_sha": prior_sha(pack_prior(plastic5["W"], {})),
        "unigram5_sha": prior_sha(unigram5),
        "gate_log": glog,
        "evals": {"gate3d": g_evals, "fivex": x_evals, "gated7": g7_evals,
                  "comp2d": c_evals, "plastic2d": p_evals,
                  "unigram": u_evals},
        "budget_per_arm": budget_arm,
        "min_edge_gate5": manifold_min(gate5["W"]),
        "row_entropy_gate5": round(manifold_row_entropy(gate5["W"]), 6),
    }
    return {"gate5": gate5, "five_x": five_x, "gated7": gated7,
            "comp5": comp5, "plastic5": plastic5, "unigram5": unigram5,
            "meta": meta}


def prior_for(cond, chains):
    if cond in ("COLD", "COLD2"):
        return "gate3d", {"W": uniform_manifold({}, get_state_context),
                          "reg": {}}
    if cond == "GATE5":
        return "gate3d", chains["gate5"]
    if cond == "GATE1_5X":
        return "gate3d", chains["five_x"]
    if cond == "GATED7":
        return "gate3d", chains["gated7"]
    if cond == "COMP5":
        return "comp2d", chains["comp5"]
    if cond == "PLASTIC5":
        return "plastic2d", chains["plastic5"]
    if cond == "UNIGRAM5":
        return "unigram", chains["unigram5"]
    sys.exit("unknown condition: %s" % cond)


def _gate_fn_of(engine):
    if engine == "gate3d":
        return get_state_context
    return gate_const


def eval_tasks(seed):
    out = []
    for lvl, k in CONFIG["eval_levels"]:
        for i in range(k):
            out.append((lvl, draw_task(lvl, seed, "target",
                                       "ev|%d|%d" % (lvl, i))))
    return out


def run_unit(cond, seed, chains, tasks):
    cfg = CONFIG
    engine, prior = prior_for(cond, chains)
    by_level = {}
    cost = 0
    macro_solves = 0
    multi_gate_solves = 0
    max_exp_depth = 0
    for j, (lvl, t) in enumerate(tasks):
        prng = XorShift64Star("ev|%s|%s|%d|%d" % (cond, seed, lvl, j))
        if engine == "unigram":
            w = prior
            prog, ev_, _e = search_task_u(t, w, cfg["eval_budget"], prng)
            cost += ev_
            if solves_u(prog, t):
                by_level[str(lvl)] = by_level.get(str(lvl), 0) + 1
                if len(prog) > max_exp_depth:
                    max_exp_depth = len(prog)
            continue
        gate_fn = _gate_fn_of(engine)
        W, reg = prior["W"], prior["reg"]
        prog, ev_, _e = search_task_gated(t, W, reg, cfg["eval_budget"],
                                          prng, gate_fn)
        cost += ev_
        if solves_tokens(prog, reg, t):
            by_level[str(lvl)] = by_level.get(str(lvl), 0) + 1
            used_macro = False
            for tok in prog:
                if tok in reg:
                    used_macro = True
            if used_macro:
                macro_solves += 1
            ref = sorted(t["train"], key=lambda e: len(e[0]))[0][0]
            gates_seen = set()
            for gk, _a, _b in gated_transitions(prog, reg, ref, gate_fn):
                gates_seen.add(gk)
            if len(gates_seen) >= 2:
                multi_gate_solves += 1
            exp = expand_tokens(prog, reg)
            if exp is not None and len(exp) > max_exp_depth:
                max_exp_depth = len(exp)
    assert cost <= len(tasks) * cfg["eval_budget"], "I0 budget violated"
    total = sum(by_level.values())
    body = {"cond": cond, "seed": seed, "engine": engine, "solved": total,
            "by_level": by_level, "cost": cost, "n_tasks": len(tasks),
            "macro_solves": macro_solves,
            "multi_gate_solves": multi_gate_solves,
            "max_exp_depth": max_exp_depth}
    if engine == "unigram":
        body["prior_sha"] = prior_sha(prior)
        body["n_macros"] = 0
    else:
        body["prior_sha"] = prior_sha(pack_prior(prior["W"], prior["reg"]))
        body["n_macros"] = len(prior["reg"])
    return body


# ---------------------------------------------------------------------------
# BATTERY / LEDGER PLUMBING
# ---------------------------------------------------------------------------

def cfg_sha():
    return hashlib.sha256(canon(CONFIG).encode()).hexdigest()[:10]


def ledger_path():
    return os.path.join(CONFIG["outdir"], "gate_%s.jsonl" % cfg_sha())


def open_ledger():
    if not os.path.isdir(CONFIG["outdir"]):
        os.makedirs(CONFIG["outdir"])
    led = Ledger(ledger_path())
    if not led.records:
        led.append("GENESIS", {
            "config": CONFIG, "prereg": PREREG,
            "source_sha": audit_sources(quiet=True)["source_sha"],
            "fingerprint": substrate_fingerprint(),
        })
    else:
        g = led.records[0]["body"]
        if canon(g["config"]) != canon(CONFIG):
            sys.exit("ledger %s was created under a different config"
                     % led.path)
    return led


def battery(seeds):
    led = open_ledger()
    g = led.records[0]["body"]
    cur = audit_sources(quiet=True)["source_sha"]
    if g["source_sha"] != cur:
        sys.exit("source sha changed since GENESIS -- new file, new ledger")
    for seed in seeds:
        if not led.find("CHAIN", seed=seed):
            print("[seed %s] building chains (gate3d / 5x / gated7 / "
                  "comp2d / plastic2d / unigram)..." % seed)
            chains = build_chains(seed)
            led.append("CHAIN", chains["meta"])
        else:
            print("[seed %s] chains in ledger; rebuilding "
                  "deterministically..." % seed)
            chains = build_chains(seed)
            if canon(chains["meta"]) != canon(
                    led.find("CHAIN", seed=seed)[0]["body"]):
                sys.exit("chain rebuild diverged from ledger -- determinism "
                         "broken or source changed")
        tasks = eval_tasks(seed)
        for cond in CONDS:
            if led.find("EVAL", cond=cond, seed=seed):
                print("  %-10s already recorded; refusing rerun" % cond)
                continue
            body = run_unit(cond, seed, chains, tasks)
            led.append("EVAL", body)
            lv = " ".join("L%s:%d" % (k, v)
                          for k, v in sorted(body["by_level"].items()))
            print("  %-10s solved %d/%d  %s  macros:%d used-in:%d "
                  "multi-gate:%d  cost %d"
                  % (cond, body["solved"], body["n_tasks"], lv or "-",
                     body["n_macros"], body["macro_solves"],
                     body["multi_gate_solves"], body["cost"]))
    print("\nbattery done -> %s" % led.path)
    print("next: python3 %s report%s" % (os.path.basename(__file__),
          " --profile smoke" if CONFIG["profile"] == "smoke" else ""))


# ---------------------------------------------------------------------------
# STATISTICS -- paired sign-flip permutation, percentile bootstrap, Holm.
# ---------------------------------------------------------------------------

def perm_p(diffs, tag, n_perm=20000):
    n = len(diffs)
    obs = sum(diffs) / float(n)
    prng = XorShift64Star("stats|perm|%s" % tag)
    hits = 0
    for _ in range(n_perm):
        s = 0.0
        for d in diffs:
            s += d if prng.unit() < 0.5 else -d
        if abs(s / n) >= abs(obs) - 1e-12:
            hits += 1
    return (hits + 1) / float(n_perm + 1), obs


def boot_ci(diffs, tag, n_boot=5000):
    n = len(diffs)
    prng = XorShift64Star("stats|boot|%s" % tag)
    means = []
    for _ in range(n_boot):
        s = 0.0
        for _i in range(n):
            s += diffs[prng.below(n)]
        means.append(s / n)
    means.sort()
    lo = means[int(0.025 * n_boot)]
    hi = means[min(int(0.975 * n_boot), n_boot - 1)]
    return lo, hi


def holm(pvals):
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    m = len(items)
    out, running = {}, 0.0
    for i, (name, p) in enumerate(items):
        adj = min(1.0, (m - i) * p)
        running = max(running, adj)
        out[name] = running
    return out


def _contrast(name, a, b):
    n = len(a)
    diffs = [a[i] - b[i] for i in range(n)]
    p, obs = perm_p(diffs, name)
    lo, hi = boot_ci(diffs, name)
    print("  %+0.3f   p = %.4f   CI [%+.3f, %+.3f]" % (obs, p, lo, hi))
    return obs, p


def report():
    led = Ledger(ledger_path())
    if not led.records:
        sys.exit("no ledger at %s -- run battery first" % ledger_path())
    per = {}
    for rec in led.find("EVAL"):
        b = rec["body"]
        per.setdefault(b["cond"], {})[b["seed"]] = b
    seeds = None
    for cond in CONDS:
        s = set(per.get(cond, {}))
        seeds = s if seeds is None else (seeds & s)
    seeds = sorted(seeds or [])
    n = len(seeds)
    if n == 0:
        sys.exit("no seed has all %d conditions yet" % len(CONDS))

    def vec(cond, lvl=None, key=None):
        out = []
        for s in seeds:
            b = per[cond][s]
            if key is not None:
                out.append(b.get(key, 0))
            elif lvl is not None:
                out.append(b["by_level"].get(str(lvl), 0))
            else:
                out.append(b["solved"])
        return out

    print("LEAPFORGE-GATED -- Expedition XVIII report")
    print("config %s (%s)   n = %d complete seeds: %s"
          % (cfg_sha(), CONFIG["profile"], n, seeds))
    print("\npre-registered: %s\n" % PREREG)
    cold = vec("COLD")
    print("%-10s %8s %8s %8s %18s" %
          ("condition", "mean", "d vs", "p", "95% CI"))
    print("%-10s %8s %8s %8s %18s" %
          ("", "solved", "COLD", "(perm)", "(bootstrap)"))
    pvals, stats = {}, {}
    for cond in CONDS:
        v = vec(cond)
        mean = sum(v) / float(n)
        if cond == "COLD":
            print("%-10s %8.3f %8s %8s %18s" % (cond, mean, "--", "--", "--"))
            continue
        diffs = [v[i] - cold[i] for i in range(n)]
        p, obs = perm_p(diffs, cond)
        lo, hi = boot_ci(diffs, cond)
        stats[cond] = (mean, obs, p, lo, hi)
        if cond != "COLD2":
            pvals[cond] = p
        print("%-10s %8.3f %+8.3f %8.4f [%+7.3f,%+7.3f]"
              % (cond, mean, obs, p, lo, hi))
    hc = holm(pvals)
    print("\nHolm-corrected p (family = all treatments vs COLD):")
    for cond in CONDS:
        if cond in hc:
            print("  %-10s p_holm = %.4f%s" % (cond, hc[cond],
                  "   *" if hc[cond] < 0.05 else ""))

    print("\nNOISE FLOOR  (COLD2 - COLD, zero-effect by construction): "
          "%+.3f  p=%.4f" % (stats["COLD2"][1], stats["COLD2"][2]))
    print("Any effect smaller in magnitude than the noise floor is "
          "uninterpretable.")

    print("\nGATING LIFT  (GATE5 - COMP5: 3D state-gated vs 2D, the ONLY "
          "difference\nis the gate function; container-richness precedent "
          "is null):")
    p_gl = _contrast("gatinglift", vec("GATE5"), vec("COMP5"))
    print("  ... on LEVEL-4 only (the pre-registered signature):")
    _contrast("gatinglift-L4", vec("GATE5", lvl=4), vec("COMP5", lvl=4))

    print("\nMACRO LIFT  (COMP5 - PLASTIC5: Expedition XVII's contrast, "
          "replicated\nin this harness):")
    p_ml = _contrast("macrolift", vec("COMP5"), vec("PLASTIC5"))

    print("\nFULL-STACK SPREAD  (GATED7 - UNIGRAM5):")
    _contrast("spread", vec("GATED7"), vec("UNIGRAM5"))

    print("\nRATCHET  (GATED7 - GATE5, does gated admission help?):")
    _contrast("ratchet", vec("GATED7"), vec("GATE5"))

    print("\nRECURSION PREMIUM  (GATE5 - GATE1_5X, compute-matched):")
    p_pr = _contrast("premium", vec("GATE5"), vec("GATE1_5X"))
    print("  ... on LEVEL-4 only:")
    _contrast("premium-L4", vec("GATE5", lvl=4), vec("GATE1_5X", lvl=4))

    print("\ndeployment (mean per unit: registry / macro-solves / "
          "multi-gate-solves /\ndeepest expanded solution):")
    for cond in CONDS:
        nm = sum(vec(cond, key="n_macros")) / float(n)
        ms = sum(vec(cond, key="macro_solves")) / float(n)
        mg = sum(vec(cond, key="multi_gate_solves")) / float(n)
        md = sum(vec(cond, key="max_exp_depth")) / float(n)
        print("  %-10s macros %4.1f   macro-solves %4.2f   "
              "multi-gate %4.2f   depth %4.1f" % (cond, nm, ms, mg, md))

    print("\nper-level mean solved (of %s per level):"
          % dict((l, k) for l, k in CONFIG["eval_levels"]))
    for cond in CONDS:
        parts = []
        for lvl, _k in CONFIG["eval_levels"]:
            vv = vec(cond, lvl=lvl)
            parts.append("L%d %.2f" % (lvl, sum(vv) / float(n)))
        print("  %-10s %s" % (cond, "  ".join(parts)))

    print("\nVERDICT:")
    if n < 40:
        print("  UNDERPOWERED (n = %d < 40): smoke run, NOT a finding. "
              "Numbers above are machinery proof only." % n)
    floor = abs(stats["COLD2"][1])
    for label, (obs, p) in (("gating lift", p_gl),
                            ("macro lift", p_ml),
                            ("recursion premium", p_pr)):
        if p < 0.05 and abs(obs) > floor and n >= 40:
            print("  %s: significant beyond the noise floor -- replicate "
                  "on fresh seeds before believing it." % label)
        else:
            print("  %s: not established at this n (obs %+.3f, p %.3f, "
                  "floor %.3f)." % (label, obs, p, floor))
    mg5 = sum(vec("GATE5", key="multi_gate_solves")) / float(n)
    if mg5 == 0.0:
        print("  NOTE: GATE5 solved nothing with a multi-gate trace -- any "
              "GATE5 effect is not the gating mechanism.")
    return 0


# ---------------------------------------------------------------------------
# REPLAY -- re-simulate every recorded unit; every hash must match.
# ---------------------------------------------------------------------------

def replay():
    led = Ledger(ledger_path())
    if not led.records:
        sys.exit("no ledger at %s" % ledger_path())
    led.verify()
    g = led.records[0]["body"]
    cur = audit_sources(quiet=True)["source_sha"]
    if g["source_sha"] != cur:
        print("WARNING: source sha differs from GENESIS -- code identity "
              "NOT proven")
    if canon(g["config"]) != canon(CONFIG):
        sys.exit("REPLAY FAIL: config drift")
    seeds = sorted({r["body"]["seed"] for r in led.find("CHAIN")})
    n_checked = 0
    for seed in seeds:
        chains = build_chains(seed)
        rec = led.find("CHAIN", seed=seed)[0]
        if canon(chains["meta"]) != canon(rec["body"]):
            sys.exit("REPLAY FAIL: CHAIN body differs (seed %s)" % seed)
        n_checked += 1
        tasks = eval_tasks(seed)
        for rec in led.find("EVAL", seed=seed):
            body = run_unit(rec["body"]["cond"], seed, chains, tasks)
            if canon(body) != canon(rec["body"]):
                sys.exit("REPLAY FAIL: EVAL %s/%s differs"
                         % (rec["body"]["cond"], seed))
            n_checked += 1
    print("REPLAY VERIFIED: %d records re-simulated bit-identically "
          "(+ chain hashes verified)" % n_checked)
    return 0


# ---------------------------------------------------------------------------
# SELFTEST -- the honesty suite: inherited invariants + G1-G5.
# ---------------------------------------------------------------------------

def _t(name, fn):
    try:
        fn()
        print("  PASS  %s" % name)
        return True
    except SystemExit as e:
        print("  FAIL  %s  (%s)" % (name, e))
        return False
    except AssertionError as e:
        print("  FAIL  %s  (%s)" % (name, e))
        return False


def selftest():
    cfg_backup = dict(CONFIG)
    ok = []

    def t01():
        a = XorShift64Star("x")
        b = XorShift64Star("x")
        c = XorShift64Star("y")
        sa = [a.u64() for _ in range(8)]
        sb = [b.u64() for _ in range(8)]
        sc = [c.u64() for _ in range(8)]
        assert sa == sb and sa != sc
    ok.append(_t("prng deterministic per tag, distinct across tags", t01))

    def t02():
        led = Ledger(None)
        led.append("A", {"v": 1})
        led.append("B", {"v": 2})
        assert led.verify() is True
        led.records[0]["body"]["v"] = 99
        tampered = False
        prev = GENESIS_PREV
        for rec in led.records:
            if rec["prev"] != prev or record_hash(prev, rec["body"]) \
                    != rec["hash"]:
                tampered = True
                break
            prev = rec["hash"]
        assert tampered, "tamper not detected"
    ok.append(_t("ledger hash chain detects tampering", t02))

    def t03():
        rep = audit_sources(quiet=True)
        assert rep["lines"] <= LINE_CAP
    ok.append(_t("source audit passes (imports/eval/line-cap/claims)", t03))

    def t04():
        f1 = substrate_fingerprint()
        assert f1 == substrate_fingerprint() and len(f1) == 16
        assert len(NAMES) == 20
        _seen, levels = build(max_depth=2)
        assert len(levels[1]) == 20 and len(levels[2]) == 294
    ok.append(_t("fingerprint stable; enumeration counts 20/294", t04))

    def t05():
        prng = XorShift64Star("t05")
        t = None
        while t is None:
            t = make_task(["inc"], prng)
        assert certify(t, 1) is True
        assert certify(t, 2) is False
        s, t_ = pool_split(3, 7)
        assert not (set(s) & set(t_))
        assert len(s) + len(t_) == len(get_ladder()[1][3])
    ok.append(_t("certify rejects mislabels; pools disjoint", t05))

    def t06():
        assert get_state_context([]) == 0
        assert get_state_context([5]) == 0
        assert get_state_context([1, 2, 3]) == 1
        assert get_state_context([10, 10, 12]) == 1
        assert get_state_context([7, 9, 8]) == 2
        assert get_state_context([200, 190, 180]) == 3
        assert get_state_context([0, 255, 0]) == 3
        prng = XorShift64Star("t06fuzz")
        for _ in range(200):
            length = prng.below(9)
            lst = [prng.below(256) for _i in range(length)]
            g1 = get_state_context(lst)
            g2 = get_state_context(list(lst))
            assert g1 == g2 and 0 <= g1 < NUM_GATES
        assert gate_const([1, 2, 3]) == 0
        assert gate_keys_for(gate_const) == ["g0"]
        assert gate_keys_for(get_state_context) == ["g0", "g1", "g2", "g3"]
    ok.append(_t("G5: gate extractor total, deterministic, in-range", t06))

    def t07():
        reg = {"m01": ["cumsum", "reverse"]}
        exp = expand_tokens(["m01", "inc"], reg)
        assert exp == ["cumsum", "reverse", "inc"]
        xs = [3, 1, 4, 1, 5]
        assert run_tokens(["m01", "inc"], reg, xs) == run(exp, xs), \
            "G4: token behaviour != expansion behaviour"
        big = {"m01": ["inc", "dec", "double"]}
        assert expand_tokens(["m01", "m01", "m01", "m01"], big) is None
        assert apply_token([], "inc", {}) == []
        assert apply_token(None, "inc", {}) == []
    ok.append(_t("G4: expansion sound, capped, total on []", t07))

    def t08():
        reg = {}
        W = uniform_manifold(reg, get_state_context)
        assert manifold_min(W) == 1.0
        assert len(W) == NUM_GATES
        # 2 programs x f=1.0 -> weight 2.0 >= THETA_UP, support 2
        scored = [(1.0, ["inc", "cumsum"], [3, 1, 4]),
                  (1.0, ["inc", "cumsum"], [9, 9, 2]),
                  (0.8, ["sort", "sort"], [5, 5])]
        reg2, new = mine_macros(scored, dict(reg))
        assert len(new) >= 1, "supported repeated sequence should register"
        W2 = grow_manifold(fit_manifold(scored, {}, get_state_context),
                           reg2)
        assert manifold_min(W2) >= 1.0, "G1: dynamic growth broke the floor"
        for gk in W2:
            for name in new:
                assert name in W2[gk], "macro row missing in slice %s" % gk
                for r in W2[gk]:
                    assert name in W2[gk][r], \
                        "macro column missing in %s/%s" % (gk, r)
        Wf = fit_manifold(scored, reg2, get_state_context)
        assert manifold_min(Wf) >= 1.0
    ok.append(_t("G1: no zero probabilities across all gate slices", t08))

    def t09():
        scored = [(1.0, ["cumsum", "reverse"], [3, 1, 4])] * 30
        Wf = fit_manifold(scored, {}, get_state_context)
        h = manifold_row_entropy(Wf)
        assert h >= 1.5, "G2: entropy collapsed to %.3f bits" % h
    ok.append(_t("G2: fitted-manifold entropy does not collapse", t09))

    def t10():
        W = uniform_manifold({}, get_state_context)
        toks = token_space({})
        ref = [3, 1, 4, 1, 5]
        path = ["cumsum", "reverse", "inc"]
        trips = gated_transitions(path, {}, ref, get_state_context)
        assert len(trips) == 3
        assert trips[0][0] == "g%d" % get_state_context(ref)

        def path_prob(Wx):
            pr = 1.0
            for gk, a, b in trips:
                pr *= Wx[gk][a][b] / sum(Wx[gk][a][c] for c in toks)
            return pr
        p0 = path_prob(W)
        _reinforce(W, trips, 2.0)
        p1 = path_prob(W)
        assert p1 > p0, "G3: reinforced gated path did not gain probability"
    ok.append(_t("G3: reinforcement is monotone on the gated path", t10))

    def t11():
        scored = [(1.0, ["inc", "cumsum"], [1, 2]),
                  (1.0, ["inc", "cumsum"], [4, 4])]
        _reg, new = mine_macros(scored, {})
        assert new, "supported repeated sequence should register"
        single = [(1.0, ["inc", "dec", "inc", "dec"], [1, 2])]
        _reg3, new3 = mine_macros(single, {})
        assert not new3, "MIN_SUPPORT=2 must block single-program macros"
        reg4 = {"m01": ["inc", "cumsum"]}
        scored4 = [(0.9, ["m01", "reverse"], [1, 2]),
                   (0.9, ["m01", "reverse"], [3, 4])]
        reg5, new5 = mine_macros(scored4, dict(reg4))
        for name in new5:
            for nm in reg5[name]:
                assert nm in PRIMS, "nested macro registered (G4)"
        many = [(1.0, [a, b], [1, 2]) for a in NAMES[:5]
                for b in NAMES[:5]] * 2
        regc, _newc = mine_macros(many, {})
        assert len(regc) <= MAX_MACROS, "registry cap exceeded"
    ok.append(_t("mining: theta/support thresholds, no nesting, cap", t11))

    def t12():
        prng = XorShift64Star("t12")
        t = None
        while t is None:
            t = make_task(["inc"], prng)
        W = uniform_manifold({}, get_state_context)
        prog, _c, _e = search_task_gated(t, W, {}, 2000,
                                         XorShift64Star("t12|s"),
                                         get_state_context)
        assert prog is not None and solves_tokens(prog, {}, t)
        W2 = uniform_manifold({}, gate_const)
        prog2, _c2, _e2 = search_task_gated(t, W2, {}, 2000,
                                            XorShift64Star("t12|c"),
                                            gate_const)
        assert prog2 is not None and solves_tokens(prog2, {}, t)
        wu = uniform_prior_u()
        prog3, _c3, _e3 = search_task_u(t, wu, 2000,
                                        XorShift64Star("t12|u"))
        assert prog3 is not None and solves_u(prog3, t)
    ok.append(_t("all three engines solve an easy certified task", t12))

    def t13():
        prng = XorShift64Star("t13")
        probes = []
        while len(probes) < 2:
            t = make_task(["inc", "reverse"], prng)
            if t:
                probes.append(t)
        W = uniform_manifold({}, get_state_context)
        acc, info = gate_ab(W, {}, copy_manifold(W), {}, probes, 300,
                            "t13gate", get_state_context)
        assert acc is False, "identical candidate must be rejected: %s" % info
    ok.append(_t("gate rejects a candidate identical to incumbent", t13))

    def t14():
        CONFIG.update({"n_rounds": 2, "src_budget": 350,
                       "src_levels": [2, 2], "gate_budget": 120,
                       "n_probe": 2, "eval_levels": [[3, 1]],
                       "eval_budget": 250, "pop_size": 16})
        ch = build_chains("t14")
        m = ch["meta"]
        for k, v in m["evals"].items():
            assert v <= m["budget_per_arm"], "I0 violated in %s" % k
        assert m["min_edge_gate5"] >= 1.0 - 1e-9
        assert ch["plastic5"]["reg"] == {}
        assert len(ch["gate5"]["W"]) == NUM_GATES
        assert len(ch["comp5"]["W"]) == 1, "2D baseline must be one slice"
        CONFIG.clear()
        CONFIG.update(cfg_backup)
    ok.append(_t("chain accounting: 6 arms, I0, slice counts, G1", t14))

    def t15():
        CONFIG.update({"n_rounds": 2, "src_budget": 350,
                       "src_levels": [2, 2], "gate_budget": 120,
                       "n_probe": 2, "eval_levels": [[3, 2]],
                       "eval_budget": 250, "pop_size": 16})
        ch = build_chains("t15")
        ts = eval_tasks("t15")
        b1 = run_unit("GATE5", "t15", ch, ts)
        b2 = run_unit("GATE5", "t15", ch, ts)
        assert canon(b1) == canon(b2), "gate3d unit not deterministic"
        b3 = run_unit("COMP5", "t15", ch, ts)
        b4 = run_unit("COMP5", "t15", ch, ts)
        assert canon(b3) == canon(b4), "comp2d unit not deterministic"
        a = run_unit("COLD", "t15", ch, ts)
        b = run_unit("COLD2", "t15", ch, ts)
        assert a["prior_sha"] == b["prior_sha"], \
            "COLD2 must share COLD's identical uniform prior"
        CONFIG.clear()
        CONFIG.update(cfg_backup)
    ok.append(_t("units bit-identical on repeat; COLD2 stream-only", t15))

    def t16():
        ps = {"a": 0.04, "b": 0.01, "c": 0.30}
        h = holm(ps)
        assert abs(h["b"] - 0.03) < 1e-9
        assert abs(h["a"] - 0.08) < 1e-9
        assert abs(h["c"] - 0.30) < 1e-9
        p, obs = perm_p([1, 1, 1, 1, 1, 1], "t16")
        assert obs == 1.0 and p < 0.05
        p2, _o = perm_p([1, -1, 1, -1, 1, -1], "t16b")
        assert p2 > 0.5
    ok.append(_t("statistics: holm + permutation sanity", t16))

    def t17():
        reg = {"m01": ["inc", "dec"]}
        W = uniform_manifold(reg, get_state_context)
        assert set(W) == {"g0", "g1", "g2", "g3"}
        for gk in W:
            assert set(W[gk]) == set(token_space(reg)) | set(start_rows())
            for r in W[gk]:
                assert set(W[gk][r]) == set(token_space(reg))
        Wc = uniform_manifold(reg, gate_const)
        assert set(Wc) == {"g0"}
        trips = gated_transitions(["inc", "sort"], {}, [5, 3, 9],
                                  gate_const)
        for gk, _a, _b in trips:
            assert gk == "g0", "constant gate must stay in slice g0"
        a = hashlib.sha256(canon(CONFIG_FULL).encode()).hexdigest()
        b = hashlib.sha256(canon(CONFIG_SMOKE).encode()).hexdigest()
        assert a != b
    ok.append(_t("3D shape correct; constant gate collapses to 2D", t17))

    def t18():
        # the gated walk actually READS the active slice: bias slice g1
        # (ordered state) toward "reverse"; a sorted ref must then draw
        # "reverse" far more often at step 1 than an unbiased slice would
        reg = {}
        toks = token_space(reg)
        W = uniform_manifold(reg, get_state_context)
        for r in W["g1"]:
            W["g1"][r]["reverse"] = 500.0
        ref = [1, 2, 3, 4]                      # gate 1 (ordered)
        prng = XorShift64Star("t18")
        hits = 0
        for _ in range(60):
            p = random_pipe(W, reg, toks, ref, get_state_context, prng)
            if p[0] == "reverse":
                hits += 1
        assert hits >= 40, "biased active slice ignored (%d/60)" % hits
        prng2 = XorShift64Star("t18")
        ref2 = [9, 1, 200]                      # gate 3 (mixed): unbiased
        hits2 = 0
        for _ in range(60):
            p = random_pipe(W, reg, toks, ref2, get_state_context, prng2)
            if p[0] == "reverse":
                hits2 += 1
        assert hits2 <= 20, "inactive slice leaked into sampling (%d/60)" \
            % hits2
    ok.append(_t("sampling reads the ACTIVE gate slice only", t18))

    CONFIG.clear()
    CONFIG.update(cfg_backup)
    n_pass = sum(1 for x in ok if x)
    print("\n%d/%d tests passed" % (n_pass, len(ok)))
    if n_pass != len(ok):
        sys.exit(1)
    print("ALL TESTS PASS")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_seeds(arg):
    out = []
    for part in arg.split(","):
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        else:
            out.append(int(part))
    return out


def _apply_profile(argv):
    if "--profile" in argv:
        name = argv[argv.index("--profile") + 1]
        if name == "smoke":
            CONFIG.clear()
            CONFIG.update(CONFIG_SMOKE)
        elif name == "full":
            CONFIG.clear()
            CONFIG.update(CONFIG_FULL)
        else:
            sys.exit("unknown profile: %s" % name)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    _apply_profile(sys.argv)
    cmd = sys.argv[1]
    if cmd == "audit":
        audit_sources()
    elif cmd == "test":
        audit_sources(quiet=True)
        selftest()
    elif cmd == "build":
        _seen, levels = get_ladder()
        print("ladder built: " + ", ".join(
            "L%d=%d" % (d, len(levels[d])) for d in sorted(levels)))
        print("substrate fingerprint = %s" % substrate_fingerprint())
    elif cmd == "battery":
        seeds = [1, 2, 3, 4, 5, 6]
        if "--seeds" in sys.argv:
            seeds = _parse_seeds(sys.argv[sys.argv.index("--seeds") + 1])
        audit_sources(quiet=True)
        battery(seeds)
    elif cmd == "report":
        report()
    elif cmd == "replay":
        replay()
    elif cmd == "sample":
        lvl = int(sys.argv[2])
        for i in range(3):
            t = draw_task(lvl, 0, "target", "sample|%d" % i)
            print("hidden pipeline : %s" % " . ".join(reversed(t["pipe"])))
            x, y = t["train"][0]
            print("example         : %s -> %s\n" % (x, y))
    else:
        print("unknown command: %s" % cmd)


if __name__ == "__main__":
    main()

# end of file -- leapforge_gated.py (xviii)
