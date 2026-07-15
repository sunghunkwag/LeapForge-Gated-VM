#!/usr/bin/env python3
"""
LEAPFORGE-OPEN -- Expedition XIX harness
========================================

THE QUESTION
------------
Expedition XVIII (leapforge_gated.py) measured search efficiency inside
a FROZEN structure: a fixed seed vocabulary and a hardcoded 4-way gate.
Expedition XIX asks a categorically different question: can the engine
EXPAND the set of tasks it can solve at all, by modifying its own
structure at runtime -- and can that expansion be machine-certified
rather than claimed?

THE JUDGE (the decisive design move)
------------------------------------
The ancestor's exhaustive enumerator (build()/sig()) can PROVE that a
task is unsolvable by the seed vocabulary at any depth <= MAX_DEPTH and
any compute budget. This file turns that prover into the admission
judge. A structural self-modification counts if and only if it makes
the engine solve a task that was certified inexpressible before the
modification (certificate C1, below). Speed improvements on
already-solvable tasks NEVER count as evidence; they are reported on
one line labeled "efficiency (not evidence)".

MECHANISM
---------
Synthesized operators are trees in a closed intermediate representation
(Op-IR), evaluated by a total, hand-written interpreter. No eval, no
exec, ever (AST-audited, same axiom as the ancestor). The gate is also
data: a threshold tree over a fixed feature vector (Gate-IR), whose
generation-0 instance reproduces the ancestor's get_state_context
exactly (proven in --selftest).

CERTIFICATES (both machine-checked, both ledgered)
--------------------------------------------------
  C1 INEXPRESSIBILITY  exhaustive breadth-first enumeration of ALL seed
     pipelines to depth MAX_DEPTH, deduplicated by the full output
     vector over the probe battery PLUS the task's own train inputs
     (anti-aliasing guard). The certificate asserts that NO enumerated
     behaviour reproduces the task's train outputs; deduplication on
     the full battery keys is sound AND complete for that check, so a
     certified task cannot even be train-matched by the unmodified
     engine, at any budget. (This is strictly stronger than requiring
     the task signature to be absent from the enumeration.)
  C2 REACHABILITY      the hidden pipeline, with each generator-only
     operator replaced by its hand-written Op-IR witness tree, must
     reproduce every train/test example through THIS file's
     interpreter. A failure to leap can never be blamed on an
     unreachable target. Witness trees live ONLY inside
     _xprim_witnesses() -- function-local, never serialized to any file
     the loop reads, unreachable from the proposal stream (proven in
     --selftest by AST inspection and registry inspection).

ADMISSION RULE (the only one that matters)
------------------------------------------
A screened operator joins the vocabulary iff adding it lets the engine
EXACTLY SOLVE >= 1 DISCOVERY task that carries a valid C1 certificate
and was unsolved before, with the new operator actually appearing in
the solving program. On admission the manifold grows by the ancestor's
grow_manifold convention (floor 1.0 everywhere -- G1 survives) and the
ledger appends the full lineage: task certificate -> operator IR ->
parent/new vocabulary sha.

SPLITS (leakage discipline)
---------------------------
  DISCOVERY  24 certified tasks; visible to the loop; drives synthesis,
             admission and gate A/Bs.
  FROZEN     12 certified tasks from a disjoint named stream; evaluated
             ONLY at generation boundaries for the headline curve;
             results never feed back into any decision.

NULL DISCIPLINE
---------------
OPEN_OFF: the identical engine with operator admission disabled, run at
identical budgets for the same number of generations. By C1 it must
score exactly 0 on certified tasks. Any nonzero is a certificate bug:
the run aborts rather than reporting a claim.

ENGINEERING CHOICES STATED PLAINLY
----------------------------------
  - The ancestor's PRIMS dict contains 20 primitives (its own selftest
    asserts len(NAMES) == 20); they are carried verbatim, so the seed
    vocabulary here is those 20 tokens. Cap: 12 admitted operators.
  - Expr arithmetic saturates at +/- 2**31 per node (totality and
    speed; invisible below that bound, and every operator application
    ends with the byte clamp).
  - COMPOSE(A, B) applies A first, then B. CONCAT(A, B) is A(x)+B(x),
    then clamped. SLICE(a, b, s) is Python x[a:b], reversed when
    s == -1. In SCAN the accumulator initializes to the first element,
    which is emitted unchanged. In ZIPSELF the ACC slot binds the
    partner element x[i+k]; out-of-range partners drop the element.
  - Screening additionally discards candidates whose output is empty on
    every probe (degenerate); admission alone still decides membership.
  - At the vocabulary cap admission halts (no eviction in XIX);
    refusals are ledgered.

LEAP COUNT (cumulative, witness-based -- the XIX.1 metric patch)
-----------------------------------------------------------------
The original XIX headline sampled frozen solves AT THE FINAL GENERATION
only; a stochastic re-search can read 0 for a task the engine provably
solved twenty times. Solvability, once witnessed, is permanent, so the
headline is now: the number of FROZEN tasks for which the ledger holds
>= 1 witness record {task_id, program tokens, vocab sha at solve time}
AND that witness re-executes exactly (all train + test examples)
through the interpreter at report time, with the operator registry
reconstructed from the ledgered ADMISSION IR -- never from live
in-memory state. A witness that fails re-execution aborts the report
as a WITNESS FAULT (it would indicate ledger corruption). The
final-generation sample is retained as one secondary legacy line.
Ledgers written before this patch lack witness programs in their GEN
records; the report derives a witness for each ledgered frozen solve
by exhaustive breadth-first enumeration over the reconstructed
vocabulary at solve time (depth <= MAX_DEPTH, deterministic order) --
the run is never re-executed. The engine itself -- search, admission,
certification, streams -- is untouched by this patch.

USAGE
-----
    python3 leapforge_open.py --selftest
    python3 leapforge_open.py --audit
    python3 leapforge_open.py --profile smoke [--seed 1]
    python3 leapforge_open.py --profile full  [--seed 1]
    python3 leapforge_open.py --replay <ledger.jsonl>
    python3 leapforge_open.py --report <ledger.jsonl>

HARD RULES
----------
  - No eval/exec, no forbidden imports, no wall-clock dependence; all
    randomness flows through SHA-256-seeded XorShift64Star streams.
  - The ancestor file leapforge_gated.py is frozen; nothing here writes
    into it and its axioms (PRIMS, probes, clamp, enumeration) are
    carried verbatim.
  - FROZEN results never influence any decision inside the loop.
  - A speedup is never an admission and never a leap.
"""

import ast
import hashlib
import json
import math
import os
import sys

VERSION = "open-xix-1.0"
LINE_CAP = 3000
MAXLEN = 24
MAX_DEPTH = 4            # program length cap in TOKENS; C1 depth bound
NUM_GATES = 4            # ancestor gate arity (generation-0 tree)
NUM_GATES_OPEN = 6       # XIX gate arity: 4 seed + 2 free slots
GATE_SHORT_LEN = 1       # ancestor gate 0: len <= this
GATE_RANGE = 15          # ancestor gate 2: max - min <= this
MAX_IR_NODES = 12        # node cap for every Op-IR tree
COST_CAP = 20000         # T3: node-evaluation cap per Op application
IR_SAT = 1 << 31         # expr saturation bound
VOCAB_CAP = 12           # max admitted operators (no eviction)
GATE_DEPTH = 3           # Gate-IR max internal depth

CONFIG_FULL = {
    "version": VERSION,
    "profile": "full",
    "n_discovery": 24,
    "n_frozen": 12,
    "budget": 2000,
    "generations": 30,
    "k_proposals": 200,
    "pop_size": 32,
    "pool_keep": 24,
    "eta": 0.5,
    "lambda": 0.90,
    "gate_period": 3,
    "stall_gens": 10,
    "outdir": "runs_open",
}

CONFIG_SMOKE = {
    "version": VERSION,
    "profile": "smoke",
    "n_discovery": 6,
    "n_frozen": 3,
    "budget": 400,
    "generations": 6,
    "k_proposals": 60,
    "pop_size": 24,
    "pool_keep": 24,
    "eta": 0.5,
    "lambda": 0.90,
    "gate_period": 3,
    "stall_gens": 10,
    "outdir": "runs_open",
}

CONFIG = dict(CONFIG_FULL)

MISSION = ("Expedition XIX: structural self-expansion under machine "
           "certification. An admission counts iff it solves a task "
           "certified inexpressible (C1) by the frozen seed vocabulary "
           "at depth <= %d; the frozen curve is the headline; OPEN_OFF "
           "is the structural floor; zero is a publishable number."
           % MAX_DEPTH)

# ancestor substrate fingerprint, asserted in --selftest (verbatim-copy
# proof: PRIMS + PROBES here hash to the same value as in the ancestor)
ANCESTOR_FINGERPRINT = "ccab00a723701e34"


# ---------------------------------------------------------------------------
# DETERMINISM -- one PRNG, text-seeded (carried VERBATIM from XVIII).
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
# SOURCE AUDIT -- forbidden imports, no dynamic eval, line cap, banned
# claims (ancestor mechanism; constants adapted: LINE_CAP=3000, positive
# import allowlist, ast.Pass ban).
# ---------------------------------------------------------------------------

FORBIDDEN_MODULES = {"random", "secrets", "numpy", "torch", "time", "pickle",
                     "multiprocessing", "threading", "socket", "subprocess"}
ALLOWED_MODULES = {"ast", "hashlib", "json", "math", "os", "sys"}


def _self_source():
    with open(os.path.abspath(__file__), "r", encoding="utf-8") as f:
        return f.read()


def _banned_words():
    # stored reversed so this file cannot trip its own detector
    rev = ["iga", "isa", "tnegreme", "ecnegreme", "ecnegilletnirepus",
           "ytiralugnis", "dednuobnu", "tneitnes", "suoicsnoc",
           "ssensuoicsnoc", "odot"]
    return [w[::-1] for w in rev]


def _source_tokens(src):
    return set("".join(c if (c.isalnum() or c == "_") else " "
                       for c in src.lower()).split())


def audit_sources(quiet=False):
    src = _self_source()
    lines = src.count("\n") + 1
    tree = ast.parse(src)
    mods, dyn, placeholders = set(), [], 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in ("eval", "exec"):
            dyn.append(node.func.id)
        elif isinstance(node, ast.Pass):
            placeholders += 1
    bad = mods & FORBIDDEN_MODULES
    if bad:
        sys.exit("AUDIT FAIL (forbidden imports): %s" % sorted(bad))
    if mods - ALLOWED_MODULES:
        sys.exit("AUDIT FAIL (import outside allowlist): %s"
                 % sorted(mods - ALLOWED_MODULES))
    if dyn:
        sys.exit("AUDIT FAIL (dynamic eval): %s" % dyn)
    if placeholders:
        sys.exit("AUDIT FAIL (placeholder statements): %d" % placeholders)
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
# LEDGER -- append-only, hash-chained (carried VERBATIM from XVIII).
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
# SEED SUBSTRATE -- Expedition XIV pipeline DSL, carried VERBATIM (axiom).
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


def get_state_context(lst):
    """Ancestor gate, carried VERBATIM. Kept as the reference for the
    generation-0 Gate-IR equivalence proof; the live engine routes all
    gating through classify(gate_tree, lst)."""
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


# ---------------------------------------------------------------------------
# OP-IR -- the open operator vocabulary. Trees are JSON-serializable
# nested lists; the interpreter is total by construction (T1), keyed by
# canonical sha (T4), deterministic (T2), and cost-capped (T3).
# Grammar (exactly this; no silent extensions):
#   Op   := MAP(Expr) | FILTER(Bool) | SCAN(Expr2) | ZIP(Expr2, shift)
#         | SLICE(a, b, step) | CAT(Op, Op) | COMP(Op, Op)
#   Expr := V | I | N | C(c) | ADD/SUB/MUL/DIV/MOD/MIN/MAX(Expr, Expr)
#         | ABS(Expr)                     (DIV=floordiv; x/0 and x%0 -> 0)
#   Expr2:= Expr + A (accumulator / ZIP partner)
#   Bool := CMP(op, Expr, Expr) | AND/OR(Bool, Bool) | NOT(Bool)
# ---------------------------------------------------------------------------

EXPR_LEAVES = ("V", "I", "N", "A", "C")
EXPR_BIN = ("ADD", "SUB", "MUL", "DIV", "MOD", "MIN", "MAX")
CMP_OPS = ("lt", "le", "eq", "ne", "ge", "gt")
OP_TAGS = ("MAP", "FILTER", "SCAN", "ZIP", "SLICE", "CAT", "COMP")


class _CostOut(Exception):
    """Interpreter cost-cap sentinel; always caught in apply_ir."""


def _sat(v):
    if v > IR_SAT:
        return IR_SAT
    if v < -IR_SAT:
        return -IR_SAT
    return v


def _ev_expr(e, v, i, n, acc, cost):
    cost[0] -= 1
    if cost[0] < 0:
        raise _CostOut()
    tag = e[0]
    if tag == "V":
        return v
    if tag == "I":
        return i
    if tag == "N":
        return n
    if tag == "A":
        return acc
    if tag == "C":
        return e[1]
    if tag == "ABS":
        a = _ev_expr(e[1], v, i, n, acc, cost)
        return -a if a < 0 else a
    a = _ev_expr(e[1], v, i, n, acc, cost)
    b = _ev_expr(e[2], v, i, n, acc, cost)
    if tag == "ADD":
        return _sat(a + b)
    if tag == "SUB":
        return _sat(a - b)
    if tag == "MUL":
        return _sat(a * b)
    if tag == "DIV":
        return _sat(a // b) if b != 0 else 0
    if tag == "MOD":
        return _sat(a % b) if b != 0 else 0
    if tag == "MIN":
        return a if a < b else b
    return a if a > b else b                       # MAX


def _ev_bool(e, v, i, n, acc, cost):
    cost[0] -= 1
    if cost[0] < 0:
        raise _CostOut()
    tag = e[0]
    if tag == "CMP":
        a = _ev_expr(e[2], v, i, n, acc, cost)
        b = _ev_expr(e[3], v, i, n, acc, cost)
        op = e[1]
        if op == "lt":
            return a < b
        if op == "le":
            return a <= b
        if op == "eq":
            return a == b
        if op == "ne":
            return a != b
        if op == "ge":
            return a >= b
        return a > b                               # gt
    if tag == "AND":
        return (_ev_bool(e[1], v, i, n, acc, cost)
                and _ev_bool(e[2], v, i, n, acc, cost))
    if tag == "OR":
        return (_ev_bool(e[1], v, i, n, acc, cost)
                or _ev_bool(e[2], v, i, n, acc, cost))
    return not _ev_bool(e[1], v, i, n, acc, cost)  # NOT


def _apply_op(t, xs, cost):
    cost[0] -= 1
    if cost[0] < 0:
        raise _CostOut()
    tag = t[0]
    n = len(xs)
    if tag == "MAP":
        return _c([_ev_expr(t[1], xs[i], i, n, 0, cost) for i in range(n)])
    if tag == "FILTER":
        return _c([xs[i] for i in range(n)
                   if _ev_bool(t[1], xs[i], i, n, 0, cost)])
    if tag == "SCAN":
        if n == 0:
            return []
        acc = xs[0]
        out = [acc]
        for i in range(1, n):
            acc = _ev_expr(t[1], xs[i], i, n, acc, cost)
            out.append(acc)
        return _c(out)
    if tag == "ZIP":
        k = t[2]
        out = []
        for i in range(n):
            j = i + k
            if 0 <= j < n:
                out.append(_ev_expr(t[1], xs[i], i, n, xs[j], cost))
        return _c(out)
    if tag == "SLICE":
        cost[0] -= n
        if cost[0] < 0:
            raise _CostOut()
        seg = list(xs[t[1]:t[2]])
        if t[3] == -1:
            seg.reverse()
        return _c(seg)
    if tag == "CAT":
        return _c(_apply_op(t[1], xs, cost) + _apply_op(t[2], xs, cost))
    return _c(_apply_op(t[2], _apply_op(t[1], xs, cost), cost))   # COMP


def apply_ir(t, xs, cap=COST_CAP):
    """T1-total application of an Op-IR tree: never raises on any list;
    exceeding the cost cap collapses the result to [] (the ancestors'
    gate-0 collapse convention)."""
    cost = [cap]
    try:
        return _apply_op(t, list(xs), cost)
    except _CostOut:
        return []


def ir_nodes(t):
    n = 1
    for ch in t:
        if isinstance(ch, list):
            n += ir_nodes(ch)
    return n


def _check_expr(e, acc_ok):
    if not isinstance(e, list) or not e or not isinstance(e[0], str):
        return False
    tag = e[0]
    if tag in ("V", "I", "N"):
        return len(e) == 1
    if tag == "A":
        return acc_ok and len(e) == 1
    if tag == "C":
        return (len(e) == 2 and isinstance(e[1], int)
                and not isinstance(e[1], bool) and -256 <= e[1] <= 256)
    if tag == "ABS":
        return len(e) == 2 and _check_expr(e[1], acc_ok)
    if tag in EXPR_BIN:
        return (len(e) == 3 and _check_expr(e[1], acc_ok)
                and _check_expr(e[2], acc_ok))
    return False


def _check_bool(e, acc_ok):
    if not isinstance(e, list) or not e or not isinstance(e[0], str):
        return False
    tag = e[0]
    if tag == "CMP":
        return (len(e) == 4 and e[1] in CMP_OPS
                and _check_expr(e[2], acc_ok) and _check_expr(e[3], acc_ok))
    if tag in ("AND", "OR"):
        return (len(e) == 3 and _check_bool(e[1], acc_ok)
                and _check_bool(e[2], acc_ok))
    if tag == "NOT":
        return len(e) == 2 and _check_bool(e[1], acc_ok)
    return False


def _check_op(t):
    if not isinstance(t, list) or not t or not isinstance(t[0], str):
        return False
    tag = t[0]
    if tag == "MAP":
        return len(t) == 2 and _check_expr(t[1], False)
    if tag == "FILTER":
        return len(t) == 2 and _check_bool(t[1], False)
    if tag == "SCAN":
        return len(t) == 2 and _check_expr(t[1], True)
    if tag == "ZIP":
        return (len(t) == 3 and _check_expr(t[1], True)
                and isinstance(t[2], int) and not isinstance(t[2], bool)
                and -4 <= t[2] <= 4)
    if tag == "SLICE":
        return (len(t) == 4
                and all(isinstance(v, int) and not isinstance(v, bool)
                        for v in t[1:])
                and -MAXLEN <= t[1] <= MAXLEN
                and -MAXLEN <= t[2] <= MAXLEN and t[3] in (1, -1))
    if tag in ("CAT", "COMP"):
        return len(t) == 3 and _check_op(t[1]) and _check_op(t[2])
    return False


def check_op(t):
    return _check_op(t) and ir_nodes(t) <= MAX_IR_NODES


def op_sha(t):
    return hashlib.sha256(canon(t).encode()).hexdigest()


def sig_ir(t):
    return tuple(tuple(apply_ir(t, p)) for p in PROBES)


# ---------------------------------------------------------------------------
# OP-IR SYNTHESIS -- the "opgen" proposal stream: random growth plus
# mutation/crossover of trees harvested from near-miss traces.
# ---------------------------------------------------------------------------

_CONST_POOL = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 16, 24, 32, 64,
               100, 128, 192, 255, -1, -2, -3, -4, -5, -7, -8, -16, -64]


def _grow_const(prng):
    if prng.unit() < 0.7:
        return prng.choice(_CONST_POOL)
    return prng.below(513) - 256


def _grow_expr(prng, budget, acc_ok):
    if budget <= 2 or prng.unit() < 0.42:
        r = prng.unit()
        if r < 0.34:
            return ["V"]
        if r < 0.46:
            return ["I"]
        if r < 0.52:
            return ["N"]
        if acc_ok and r < 0.72:
            return ["A"]
        return ["C", _grow_const(prng)]
    if prng.unit() < 0.08:
        return ["ABS", _grow_expr(prng, budget - 1, acc_ok)]
    tag = prng.choice(EXPR_BIN)
    left = _grow_expr(prng, (budget - 1) // 2, acc_ok)
    right = _grow_expr(prng, budget - 1 - ir_nodes(left), acc_ok)
    return [tag, left, right]


def _grow_bool(prng, budget, acc_ok):
    """Budget-safe: never returns more than max(budget, 3) nodes; every
    call site guarantees budget >= 3 (a CMP over two leaves)."""
    if budget >= 7 and prng.unit() < 0.12:
        r = prng.unit()
        if r < 0.4:
            inner = _grow_bool(prng, budget - 1, acc_ok)
            return ["NOT", inner]
        tag = "AND" if r < 0.7 else "OR"
        left = _grow_bool(prng, (budget - 1) // 2, acc_ok)
        right = _grow_bool(prng, budget - 1 - ir_nodes(left), acc_ok)
        return [tag, left, right]
    left = _grow_expr(prng, (budget - 1) // 2, acc_ok)
    right = _grow_expr(prng, budget - 1 - ir_nodes(left), acc_ok)
    return ["CMP", prng.choice(CMP_OPS), left, right]


def grow_op(prng, budget=MAX_IR_NODES):
    """Budget-safe by construction: every branch is gated on the node
    budget it needs, so grow_op(b) returns at most b nodes for b >= 1
    (asserted over a budget sweep in --selftest)."""
    r = prng.unit()
    if budget >= 6 and r < 0.08:
        left = grow_op(prng, (budget - 1) // 2)
        right = grow_op(prng, budget - 1 - ir_nodes(left))
        return ["CAT", left, right]
    if budget >= 6 and r < 0.16:
        left = grow_op(prng, (budget - 1) // 2)
        right = grow_op(prng, budget - 1 - ir_nodes(left))
        return ["COMP", left, right]
    if budget >= 2 and r < 0.50:
        return ["MAP", _grow_expr(prng, budget - 1, False)]
    if budget >= 4 and r < 0.64:
        return ["FILTER", _grow_bool(prng, budget - 1, False)]
    if budget >= 2 and r < 0.77:
        return ["SCAN", _grow_expr(prng, budget - 1, True)]
    if budget >= 3 and r < 0.90:
        return ["ZIP", _grow_expr(prng, budget - 2, True),
                prng.below(9) - 4]
    a = prng.below(2 * MAXLEN + 1) - MAXLEN
    b = prng.below(2 * MAXLEN + 1) - MAXLEN
    return ["SLICE", a, b, 1 if prng.unit() < 0.5 else -1]


def _subtrees(t, path=()):
    """All (path, subtree) pairs of list-nodes inside an Op-IR tree."""
    out = [(path, t)]
    for idx, ch in enumerate(t):
        if isinstance(ch, list):
            out.extend(_subtrees(ch, path + (idx,)))
    return out


def _node_kind(t):
    tag = t[0]
    if tag in OP_TAGS:
        return "op"
    if tag in ("CMP", "AND", "OR", "NOT"):
        return "bool"
    return "expr"


def _replace_at(t, path, sub):
    if not path:
        return sub
    out = list(t)
    out[path[0]] = _replace_at(out[path[0]], path[1:], sub)
    return out


def _copy_ir(t):
    return [(_copy_ir(ch) if isinstance(ch, list) else ch) for ch in t]


def mutate_ir(t, prng):
    """One structural or parametric edit; falls back to fresh growth if
    the mutant fails validation or the node cap."""
    t = _copy_ir(t)
    nodes = _subtrees(t)
    path, sub = nodes[prng.below(len(nodes))]
    tag = sub[0]
    r = prng.unit()
    if tag == "C" and r < 0.6:
        c = sub[1] + prng.choice([-4, -2, -1, 1, 2, 4])
        mut = _replace_at(t, path, ["C", max(-256, min(256, c))])
    elif tag == "CMP" and r < 0.5:
        mut = _replace_at(t, path, [tag, prng.choice(CMP_OPS)] + sub[2:])
    elif tag == "ZIP" and r < 0.5:
        k = max(-4, min(4, sub[2] + prng.choice([-1, 1])))
        mut = _replace_at(t, path, [tag, sub[1], k])
    elif tag == "SLICE" and r < 0.6:
        a = max(-MAXLEN, min(MAXLEN, sub[1] + prng.choice([-2, -1, 1, 2])))
        b = max(-MAXLEN, min(MAXLEN, sub[2] + prng.choice([-2, -1, 1, 2])))
        s = sub[3] if prng.unit() < 0.7 else -sub[3]
        mut = _replace_at(t, path, [tag, a, b, s])
    else:
        kind = _node_kind(sub)
        room = MAX_IR_NODES - (ir_nodes(t) - ir_nodes(sub))
        if room < 1 or (kind == "bool" and room < 3):
            return grow_op(prng)
        if kind == "op":
            fresh = grow_op(prng, room)
        elif kind == "bool":
            fresh = _grow_bool(prng, room, True)
        else:
            fresh = _grow_expr(prng, room, True)
        mut = _replace_at(t, path, fresh)
    if check_op(mut):
        return mut
    return grow_op(prng)


def crossover_ir(a, b, prng):
    """Graft a same-kind subtree of b into a; falls back to mutation."""
    a = _copy_ir(a)
    na = _subtrees(a)
    path, sub = na[prng.below(len(na))]
    kind = _node_kind(sub)
    donors = [s for _p, s in _subtrees(b) if _node_kind(s) == kind]
    if donors:
        child = _replace_at(a, path, _copy_ir(donors[prng.below(len(donors))]))
        if check_op(child):
            return child
    return mutate_ir(a, prng)


# ---------------------------------------------------------------------------
# GATE-IR -- open state classifier. Feature vector phi(list) is fixed,
# total, O(n), integer-valued. Trees are binary threshold trees of
# depth <= GATE_DEPTH with leaves in [0, NUM_GATES_OPEN).
# ---------------------------------------------------------------------------

PHI_RANGES = [(0, MAXLEN), (0, 1), (0, 255), (0, 255), (0, MAXLEN),
              (0, 16), (0, MAXLEN)]


def phi(lst):
    """[len, is_monotone_nondec, max-min, mean, num_distinct,
    even_ratio*16 (int), max_runlength] -- all integers, total, O(n)."""
    n = len(lst)
    if n == 0:
        return [0, 1, 0, 0, 0, 0, 0]
    mono = 1
    i = 1
    while i < n:
        if lst[i] < lst[i - 1]:
            mono = 0
            break
        i += 1
    lo = lst[0]
    hi = lst[0]
    tot = 0
    ev = 0
    for v in lst:
        if v < lo:
            lo = v
        if v > hi:
            hi = v
        tot += v
        if v % 2 == 0:
            ev += 1
    rmax, cur = 1, 1
    for i in range(1, n):
        if lst[i] == lst[i - 1]:
            cur += 1
            if cur > rmax:
                rmax = cur
        else:
            cur = 1
    return [n, mono, hi - lo, tot // n, len(set(lst)), (ev * 16) // n, rmax]


def gen0_gate_tree():
    """Generation-0 Gate-IR: reproduces the ancestor's
    get_state_context EXACTLY (proven in --selftest over the probe
    battery plus 10,000 fuzz lists)."""
    return ["N", 0, GATE_SHORT_LEN,
            ["L", 0],
            ["N", 1, 0,
             ["N", 2, GATE_RANGE, ["L", 2], ["L", 3]],
             ["L", 1]]]


def classify(tree, lst):
    f = phi(lst)
    node = tree
    while node[0] == "N":
        node = node[3] if f[node[1]] <= node[2] else node[4]
    return node[1]


def _check_gate(node, depth):
    if not isinstance(node, list) or not node:
        return False
    if node[0] == "L":
        return (len(node) == 2 and isinstance(node[1], int)
                and 0 <= node[1] < NUM_GATES_OPEN)
    if node[0] == "N":
        if depth >= GATE_DEPTH or len(node) != 5:
            return False
        if not (isinstance(node[1], int) and 0 <= node[1] < len(PHI_RANGES)):
            return False
        if not isinstance(node[2], int):
            return False
        return (_check_gate(node[3], depth + 1)
                and _check_gate(node[4], depth + 1))
    return False


def check_gate(tree):
    return _check_gate(tree, 0)


def gate_sha(tree):
    return hashlib.sha256(canon(tree).encode()).hexdigest()[:16]


def _gate_paths(node, path=(), depth=0):
    out = [(path, node, depth)]
    if node[0] == "N":
        out.extend(_gate_paths(node[3], path + (3,), depth + 1))
        out.extend(_gate_paths(node[4], path + (4,), depth + 1))
    return out


def mutate_gate(tree, prng):
    """1-2 edits: threshold tweak, feature swap, leaf relabel, leaf
    split (depth permitting), or subtree collapse."""
    out = json.loads(canon(tree))
    for _ in range(1 + prng.below(2)):
        paths = _gate_paths(out)
        path, node, depth = paths[prng.below(len(paths))]
        r = prng.unit()
        if node[0] == "N":
            if r < 0.40:
                lo, hi = PHI_RANGES[node[1]]
                thr = node[2] + prng.choice([-4, -2, -1, 1, 2, 4])
                sub = [node[0], node[1], max(lo, min(hi, thr)),
                       node[3], node[4]]
            elif r < 0.70:
                feat = prng.below(len(PHI_RANGES))
                lo, hi = PHI_RANGES[feat]
                sub = ["N", feat, lo + prng.below(hi - lo + 1),
                       node[3], node[4]]
            else:
                keep = node[3] if prng.unit() < 0.5 else node[4]
                sub = json.loads(canon(keep))
        else:
            if r < 0.5 or depth >= GATE_DEPTH:
                sub = ["L", prng.below(NUM_GATES_OPEN)]
            else:
                feat = prng.below(len(PHI_RANGES))
                lo, hi = PHI_RANGES[feat]
                sub = ["N", feat, lo + prng.below(hi - lo + 1),
                       ["L", node[1]], ["L", prng.below(NUM_GATES_OPEN)]]
        cand = _replace_at(out, path, sub)
        if check_gate(cand):
            out = cand
    return out


# ---------------------------------------------------------------------------
# OPEN ENGINE -- token space = 20 seed prims + admitted operators.
# The gated EA search is the ancestor's search_task_gated convention
# (local plasticity eta*delta_f*xi, decay lambda toward base, floor 1.0)
# with the registry replaced by atomic Op-IR tokens and the gate
# replaced by Gate-IR classification.
# ---------------------------------------------------------------------------

GKEYS_OPEN = ["g%d" % i for i in range(NUM_GATES_OPEN)]


def token_space_open(ops):
    return NAMES + sorted(ops)


def apply_token_open(v, tok, ops):
    """Advance a list state by one token; total on every input."""
    if v is None:
        return []
    if tok in ops:
        return apply_ir(ops[tok]["ir"], v)
    return PRIMS[tok](list(v))


def run_tokens_open(pipe, ops, xs):
    v = list(xs)
    for tok in pipe:
        v = apply_token_open(v, tok, ops)
    return v


def _start_key(depth):
    d = depth if depth >= 1 else 1
    d = MAX_DEPTH if d > MAX_DEPTH else d
    return "<S%d>" % d


def start_rows():
    return [_start_key(d) for d in range(1, MAX_DEPTH + 1)]


def manifold_rows_open(ops):
    return token_space_open(ops) + start_rows()


def uniform_manifold_open(ops):
    toks = token_space_open(ops)
    rows = manifold_rows_open(ops)
    return {gk: {r: {c: 1.0 for c in toks} for r in rows}
            for gk in GKEYS_OPEN}


def copy_manifold(W):
    return {gk: {r: dict(W[gk][r]) for r in W[gk]} for gk in W}


def grow_manifold_open(W, ops):
    """Dynamic expansion at operator admission: every gate slice gets a
    floor-weight column in every row and a floor-weight row per new
    token (G1 by construction); learned weights are preserved.
    Ancestor's grow_manifold convention, verbatim in shape."""
    toks = token_space_open(ops)
    rows = manifold_rows_open(ops)
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


def gated_transitions_open(pipe, ops, ref, gtree):
    if not pipe:
        return []
    out = []
    v = list(ref)
    prev = _start_key(len(pipe))
    for tok in pipe:
        gk = "g%d" % classify(gtree, v)
        out.append((gk, prev, tok))
        v = apply_token_open(v, tok, ops)
        prev = tok
    return out


def fit_manifold_open(scored, ops, gtree, keep=None, strength=3.0):
    keep = keep or CONFIG["pool_keep"]
    W = uniform_manifold_open(ops)
    toks = set(token_space_open(ops))
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
        for gk, a, b in gated_transitions_open(prog, ops, ref, gtree):
            W[gk][a][b] = W[gk][a][b] + strength * f
    return W


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


def random_pipe(W, ops, toks, ref, gtree, prng):
    depth = 1 + prng.below(MAX_DEPTH)
    out = []
    v = list(ref)
    prev = _start_key(depth)
    for _ in range(depth):
        gk = "g%d" % classify(gtree, v)
        nm = sample_next(gk, prev, W, toks, prng)
        out.append(nm)
        v = apply_token_open(v, nm, ops)
        prev = nm
    return out


def _state_at(pipe, k, ops, ref):
    v = list(ref)
    for i in range(k):
        v = apply_token_open(v, pipe[i], ops)
    return v


def mutate_pipe(pipe, W, ops, toks, ref, gtree, prng):
    p = list(pipe)
    for _ in range(1 + prng.below(2)):
        r = prng.unit()
        if r < 0.35 and len(p) < MAX_DEPTH:
            k = prng.below(len(p) + 1)
            prev = p[k - 1] if k > 0 else _start_key(len(p) + 1)
            gk = "g%d" % classify(gtree, _state_at(p, k, ops, ref))
            p.insert(k, sample_next(gk, prev, W, toks, prng))
        elif r < 0.65 and len(p) > 1:
            p.pop(prng.below(len(p)))
        elif p:
            k = prng.below(len(p))
            prev = p[k - 1] if k > 0 else _start_key(len(p))
            gk = "g%d" % classify(gtree, _state_at(p, k, ops, ref))
            p[k] = sample_next(gk, prev, W, toks, prng)
    if not p:
        gk = "g%d" % classify(gtree, list(ref))
        p = [sample_next(gk, _start_key(1), W, toks, prng)]
    return p


def crossover(p1, p2, prng):
    c = p1[:prng.below(len(p1) + 1)] + p2[prng.below(len(p2) + 1):]
    c = c[:MAX_DEPTH]
    return c if c else list(p1[:1] or p2[:1])


def check_exact_open(pipe, ops, examples):
    for x, y in examples:
        if run_tokens_open(pipe, ops, x) != y:
            return False
    return True


def fitness_open(pipe, ops, examples):
    tot = 0.0
    for x, y in examples:
        out = run_tokens_open(pipe, ops, x)
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


def search_task_open(task, W_base, ops, budget, prng, gtree):
    """Population EA over token pipelines with a state-gated local
    manifold; ancestor's search_task_gated convention. Returns
    (program|None, evals_used, elite_pool)."""
    ps = CONFIG["pop_size"]
    eta = CONFIG["eta"]
    lam = CONFIG["lambda"]
    xi = float(task["level"]) / float(MAX_DEPTH)
    toks = token_space_open(ops)
    guide = sorted(task["train"], key=lambda e: len(e[0]))[:2]
    ref = guide[0][0]
    W_loc = copy_manifold(W_base)
    evals = [0]
    best_f = [0.0]

    def ev(p):
        evals[0] += 1
        f = fitness_open(p, ops, guide)
        if eta > 0.0 and f > best_f[0]:
            trips = gated_transitions_open(p, ops, ref, gtree)
            _reinforce(W_loc, trips, eta * (f - best_f[0]) * xi)
        if f > best_f[0]:
            best_f[0] = f
        return f

    pop = []
    while len(pop) < ps and evals[0] < budget:
        p = random_pipe(W_loc, ops, toks, ref, gtree, prng)
        f = ev(p)
        if f >= 1.0 and check_exact_open(p, ops, task["train"]):
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
                c = random_pipe(W_loc, ops, toks, ref, gtree, prng)
            elif r < 0.65:
                c = mutate_pipe(_tournament(pop, prng)[1], W_loc, ops,
                                toks, ref, gtree, prng)
            else:
                c = crossover(_tournament(pop, prng)[1],
                              _tournament(pop, prng)[1], prng)
            f = ev(c)
            if f >= 1.0 and check_exact_open(c, ops, task["train"]):
                return c, evals[0], [(f2, p2) for f2, p2 in elite[:12]]
            newpop.append((f, c))
        pop = newpop
    pop.sort(key=lambda t: -t[0])
    return None, evals[0], [(f, p) for f, p in pop[:12]]


def solves_open(pipe, ops, task):
    return (pipe is not None
            and check_exact_open(pipe, ops, task["train"])
            and check_exact_open(pipe, ops, task["test"]))


# ---------------------------------------------------------------------------
# XPRIMS -- 12 generator-only operators, hidden from the searcher (they
# never enter the token space). Each is expressible in Op-IR via a
# hand-written witness tree (C2), and each certified task built from
# them is proven seed-inexpressible (C1). Final definitions are
# ledgered by behaviour sha.
# ---------------------------------------------------------------------------

XPRIMS = {
    "square":  lambda x: _c([v * v for v in x]),
    "absdiff": lambda x: _c([x[0]] + [abs(x[i] - x[i - 1])
                             for i in range(1, len(x))]) if x else [],
    "pairmax": lambda x: _c([max(x[i], x[i + 1])
                             for i in range(len(x) - 1)]),
    "triple":  lambda x: _c([v * 3 for v in x]),
    "sub7":    lambda x: _c([v - 7 for v in x]),
    "clip64":  lambda x: _c([min(v, 64) for v in x]),
    "stride2": lambda x: _c(x[::2]),
    "revtail": lambda x: _c([x[0]] + list(reversed(x[1:]))) if x else [],
    "scanmin": lambda x: _c([min(x[:i + 1]) for i in range(len(x))]),
    "gapfill": lambda x: _c([x[i] + (i - x[i] % 4)
                             for i in range(len(x))]),
    "mirror":  lambda x: _c(list(x) + list(reversed(x))),
    "oddkeep": lambda x: _c([v for v in x if v % 2 == 1]),
}
XNAMES = sorted(XPRIMS)


def _xprim_witnesses():
    """Op-IR witness trees for the XPRIMS -- C2 reachability proofs.
    ISOLATION (leakage discipline, non-negotiable): this table is built
    fresh inside this function on every call, is never stored in a
    module global, is never serialized into the ledger or any other
    file the loop reads, and is called ONLY by certify_c2 and the
    selftest (proven in --selftest by AST inspection of this source and
    by registry inspection). The proposal stream cannot reach it."""
    return {
        "square":  ["MAP", ["MUL", ["V"], ["V"]]],
        "absdiff": ["CAT", ["SLICE", 0, 1, 1],
                    ["ZIP", ["ABS", ["SUB", ["V"], ["A"]]], -1]],
        "pairmax": ["ZIP", ["MAX", ["V"], ["A"]], 1],
        "triple":  ["MAP", ["MUL", ["V"], ["C", 3]]],
        "sub7":    ["MAP", ["SUB", ["V"], ["C", 7]]],
        "clip64":  ["MAP", ["MIN", ["V"], ["C", 64]]],
        "stride2": ["FILTER", ["CMP", "eq", ["MOD", ["I"], ["C", 2]],
                               ["C", 0]]],
        "revtail": ["CAT", ["SLICE", 0, 1, 1], ["SLICE", 1, MAXLEN, -1]],
        "scanmin": ["SCAN", ["MIN", ["A"], ["V"]]],
        "gapfill": ["MAP", ["ADD", ["V"], ["SUB", ["I"],
                            ["MOD", ["V"], ["C", 4]]]]],
        "mirror":  ["CAT", ["SLICE", 0, MAXLEN, 1],
                    ["SLICE", 0, MAXLEN, -1]],
        "oddkeep": ["FILTER", ["CMP", "eq", ["MOD", ["V"], ["C", 2]],
                               ["C", 1]]],
    }


def run_hidden(pipe, xs):
    """Generator-side execution of a hidden pipeline (XPRIMS + at most
    one seed primitive); total on every byte list."""
    v = list(xs)
    for nm in pipe:
        v = XPRIMS[nm](v) if nm in XPRIMS else PRIMS[nm](list(v))
    return v


# ---------------------------------------------------------------------------
# CERTIFICATES -- C1 (inexpressibility) and C2 (reachability).
# ---------------------------------------------------------------------------

def enum_battery(battery, max_depth=MAX_DEPTH):
    """Exhaustive BFS over ALL seed pipelines to max_depth, dedup by
    the full output vector on `battery` (the ancestor's build()/sig()
    machinery generalized to an arbitrary input battery). Dedup on the
    full key is sound and complete: two pipelines with identical
    battery outputs stay identical under every extension. Returns
    (set of behaviour keys, per-depth counts, enum fingerprint sha)."""
    base = tuple(tuple(_c(list(x))) for x in battery)
    seen = {base}
    frontier = [base]
    counts = {}
    h = hashlib.sha256(canon([[list(o) for o in base]]).encode())
    for d in range(1, max_depth + 1):
        nxt = []
        for outs in frontier:
            for nm in NAMES:
                fn = PRIMS[nm]
                cand = tuple(tuple(fn(list(o))) for o in outs)
                if cand in seen:
                    continue
                seen.add(cand)
                nxt.append(cand)
                h.update(canon([[list(o) for o in cand]]).encode())
        frontier = nxt
        counts[d] = len(nxt)
    return seen, counts, h.hexdigest()


def certify_c1(task):
    """C1 INEXPRESSIBILITY: no seed pipeline of depth <= MAX_DEPTH
    reproduces the task's train outputs. Battery = standard probes PLUS
    the task's own train inputs (anti-aliasing guard). Returns the
    certificate body, or None when some seed behaviour matches (task
    must be discarded)."""
    train_in = [x for x, _y in task["train"]]
    train_out = tuple(tuple(y) for _x, y in task["train"])
    battery = [list(p) for p in PROBES] + [list(x) for x in train_in]
    seen, counts, enum_sha = enum_battery(battery, MAX_DEPTH)
    k = len(PROBES)
    for key in seen:
        if key[k:] == train_out:
            return None
    body = {
        "kind": "C1",
        "depth": MAX_DEPTH,
        "battery_sha": hashlib.sha256(canon(battery).encode()).hexdigest(),
        "task_sha": hashlib.sha256(
            canon([[list(x), list(y)] for x, y in
                   task["train"] + task["test"]]).encode()).hexdigest(),
        "enum_sha": enum_sha,
        "n_behaviors": len(seen),
        "counts": counts,
    }
    body["cert_sha"] = hashlib.sha256(canon(body).encode()).hexdigest()
    return body


def certify_c2(task):
    """C2 REACHABILITY: the hidden pipeline with every XPRIM replaced
    by its Op-IR witness (seed primitives kept native, exactly as the
    engine's token space would execute them) reproduces every
    train/test example through THIS file's interpreter. Returns the
    certificate body, or None on mismatch. Witness trees never leave
    this function's frame."""
    wit = _xprim_witnesses()
    for x, y in task["train"] + task["test"]:
        v = list(x)
        for nm in task["pipe"]:
            if nm in XPRIMS:
                v = apply_ir(wit[nm], v)
            else:
                v = PRIMS[nm](list(v))
        if v != y:
            return None
    body = {
        "kind": "C2",
        "task_sha": hashlib.sha256(
            canon([[list(x), list(y)] for x, y in
                   task["train"] + task["test"]]).encode()).hexdigest(),
        "pipe_len": len(task["pipe"]),
        "ok": True,
    }
    body["cert_sha"] = hashlib.sha256(canon(body).encode()).hexdigest()
    return body


def draw_hidden_pipe(prng):
    r = prng.unit()
    length = 1 if r < 0.45 else (2 if r < 0.80 else 3)
    pipe = [XNAMES[prng.below(len(XNAMES))] for _ in range(length)]
    if length >= 2 and prng.unit() < 0.35:
        pipe[prng.below(length)] = NAMES[prng.below(len(NAMES))]
    return pipe


def make_task_open(pipe, prng, n_train=4, n_test=4):
    """Task format identical to the ancestor's make_task (train lengths
    3-6, test lengths 7-11, byte values), hidden pipeline run through
    the generator-side XPRIMS."""
    def mk(lo, hi, n):
        out = []
        for _ in range(n):
            length = lo + prng.below(hi - lo + 1)
            out.append([prng.below(256) for _ in range(length)])
        return out
    tr_in, te_in = mk(3, 6, n_train), mk(7, 11, n_test)
    tr = [(x, run_hidden(pipe, x)) for x in tr_in]
    te = [(x, run_hidden(pipe, x)) for x in te_in]
    if all(len(o) == 0 for _x, o in tr):
        return None
    if all(o == x for x, o in tr):
        return None
    if any(len(o) == 0 for _x, o in tr + te) and \
            sum(1 for _x, o in tr + te if len(o) == 0) > 2:
        return None
    return {"train": tr, "test": te, "pipe": list(pipe), "level": len(pipe)}


def gen_certified_tasks(count, stream, id_prefix, split, led, max_tries=600):
    """Draw tasks until `count` carry BOTH certificates; discard the
    rest. Every accepted task is ledgered with its data and both
    certificate shas (witness trees are never serialized)."""
    prng = XorShift64Star(stream)
    out = []
    tries = 0
    while len(out) < count:
        tries += 1
        if tries > max_tries:
            sys.exit("task generation exhausted (%s)" % stream)
        pipe = draw_hidden_pipe(prng)
        task = make_task_open(pipe, prng)
        if task is None:
            continue
        c2 = certify_c2(task)
        if c2 is None:
            continue
        c1 = certify_c1(task)
        if c1 is None:
            continue
        tid = "%s%02d" % (id_prefix, len(out))
        task["id"] = tid
        task["c1"] = c1
        task["c2"] = c2
        out.append(task)
        led.append("TASK", {
            "id": tid, "split": split, "pipe": list(pipe),
            "level": task["level"],
            "train": [[list(x), list(y)] for x, y in task["train"]],
            "test": [[list(x), list(y)] for x, y in task["test"]],
            "c1_sha": c1["cert_sha"], "c1_behaviors": c1["n_behaviors"],
            "c1_enum_sha": c1["enum_sha"], "c2_sha": c2["cert_sha"],
        })
    return out


# ---------------------------------------------------------------------------
# GENERATIONAL LOOP -- the runnable core.
# ---------------------------------------------------------------------------

def vocab_sha(ops):
    return hashlib.sha256(
        canon([[nm, ops[nm]["sha"]] for nm in sorted(ops)])
        .encode()).hexdigest()[:16]


def _harvest_open(pool, prog, elite, ref):
    if prog is not None:
        pool.append((1.0, list(prog), list(ref)))
    for f, p in elite[:3]:
        if f > 0.0:
            pool.append((f, list(p), list(ref)))


def _seed_sigs():
    out = {IDENT}
    for nm in NAMES:
        out.add(sig([nm]))
    return out


_EMPTY_SIG = tuple(() for _ in PROBES)

CAND_TOKEN = "zzcand"
CAND_POOL_CAP = 40


def propose_ops(opgen, cand_pool, unsolved_idx, k, ops):
    """Phase 2: K proposals from the dedicated "opgen" stream -- fresh
    random growth mixed with mutation/crossover of trees harvested from
    near-miss traces (the candidate pool plus admitted operators that
    appeared in near-miss elites). Screening: T1-T3 by construction of
    the interpreter, behavioural novelty vs seeds, registered ops,
    identity and this batch; degenerate all-empty behaviour dropped."""
    known = _seed_sigs()
    for nm in sorted(ops):
        known.add(sig_ir(ops[nm]["ir"]))
    batch, screened = set(), []
    harvest = [(s, ir, ti) for s, ir, ti in cand_pool]
    for i in range(k):
        if not unsolved_idx:
            break
        if harvest and opgen.unit() < 0.5:
            j = opgen.below(min(len(harvest), 12))
            base_s, base_ir, base_ti = harvest[j]
            if len(harvest) >= 2 and opgen.unit() < 0.35:
                j2 = opgen.below(min(len(harvest), 12))
                ir = crossover_ir(base_ir, harvest[j2][1], opgen)
            else:
                ir = mutate_ir(base_ir, opgen)
            ti = base_ti if base_ti in unsolved_idx else \
                unsolved_idx[i % len(unsolved_idx)]
        else:
            ir = grow_op(opgen)
            ti = unsolved_idx[i % len(unsolved_idx)]
        if not check_op(ir):
            continue
        s = sig_ir(ir)
        if s in known or s in batch or s == _EMPTY_SIG:
            continue
        batch.add(s)
        screened.append((ir, op_sha(ir), ti))
    return screened


def run_arm(tasks_d, tasks_f, gens, admission_on, arm, seed, led,
            quiet=False):
    """One arm of the expedition: OPEN (admission live) or OPEN_OFF
    (identical engine and budgets, admission disabled -- the structural
    floor). FROZEN results are recorded for the curve and NEVER feed
    back into any decision."""
    cfg = CONFIG
    B = cfg["budget"]
    ops = {}
    gtree = gen0_gate_tree()
    W = uniform_manifold_open(ops)
    pool = []
    cand_pool = []
    solved = {}
    best_f = {t["id"]: 0.0 for t in tasks_d}
    opgen = XorShift64Star("opgen|%s|%s" % (arm, seed))
    frozen_curve = []
    evals_arm = 0
    n_admissions = 0
    stall = 0
    gens_run = 0
    stop_reason = "generations_exhausted"
    for g in range(1, gens + 1):
        gens_run = g
        gen_evals = 0
        newly_solved = []
        attempts = []

        # (1) attempt every unsolved DISCOVERY task
        for ti, t in enumerate(tasks_d):
            if t["id"] in solved:
                continue
            prng = XorShift64Star("search:g%d:t%d|%s|%s"
                                  % (g, ti, arm, seed))
            prog, ev_, elite = search_task_open(t, W, ops, B, prng, gtree)
            gen_evals += ev_
            if prog is not None and solves_open(prog, ops, t):
                solved[t["id"]] = {"gen": g, "prog": list(prog),
                                   "via": "vocab"}
                newly_solved.append(t["id"])
                ref = sorted(t["train"], key=lambda e: len(e[0]))[0][0]
                _harvest_open(pool, prog, elite, ref)
                attempts.append([t["id"], ev_, 1])
            else:
                ref = sorted(t["train"], key=lambda e: len(e[0]))[0][0]
                _harvest_open(pool, None, elite, ref)
                if elite and elite[0][0] > best_f[t["id"]]:
                    best_f[t["id"]] = elite[0][0]
                attempts.append([t["id"], ev_, 0])

        # (2) propose + screen K candidate operators
        unsolved_idx = [ti for ti, t in enumerate(tasks_d)
                        if t["id"] not in solved]
        screened = propose_ops(opgen, cand_pool, unsolved_idx,
                               cfg["k_proposals"], ops)

        # (3) re-attempt each candidate's associated failing task
        admissions_gen = []
        refusals_gen = []
        for ci, (ir, sha, ti) in enumerate(screened):
            t = tasks_d[ti]
            if t["id"] in solved:
                continue
            ops_plus = dict(ops)
            ops_plus[CAND_TOKEN] = {"ir": ir, "sha": sha}
            Wc = grow_manifold_open(W, ops_plus)
            prng = XorShift64Star("cand:g%d:c%d:t%d|%s|%s"
                                  % (g, ci, ti, arm, seed))
            prog, ev_, elite = search_task_open(t, Wc, ops_plus, B, prng,
                                                gtree)
            gen_evals += ev_
            solving = (prog is not None and solves_open(prog, ops_plus, t))
            if solving and CAND_TOKEN in prog:
                if not admission_on:
                    refusals_gen.append({"op_sha": sha, "task": t["id"],
                                         "reason": "admission_disabled"})
                    continue
                if len(ops) >= VOCAB_CAP:
                    refusals_gen.append({"op_sha": sha, "task": t["id"],
                                         "reason": "vocab_cap"})
                    continue
                parent_sha = vocab_sha(ops)
                name = "o%02d" % (len(ops) + 1)
                ops[name] = {"ir": _copy_ir(ir), "sha": sha}
                W = grow_manifold_open(W, ops)
                prog_named = [name if tok == CAND_TOKEN else tok
                              for tok in prog]
                solved[t["id"]] = {"gen": g, "prog": prog_named,
                                   "via": name}
                newly_solved.append(t["id"])
                ref = sorted(t["train"], key=lambda e: len(e[0]))[0][0]
                pool.append((1.0, prog_named, list(ref)))
                n_admissions += 1
                admissions_gen.append(name)
                led.append("ADMISSION", {
                    "arm": arm, "gen": g, "op": name, "op_sha": sha,
                    "ir": ir, "solved_task_id": t["id"],
                    "certificate_sha": t["c1"]["cert_sha"],
                    "parent_vocab_sha": parent_sha,
                    "new_vocab_sha": vocab_sha(ops),
                    "program": prog_named,
                })
            elif solving:
                # solved by the incumbent vocabulary alone (late solve);
                # no admission evidence for the candidate
                solved[t["id"]] = {"gen": g, "prog": list(prog),
                                   "via": "vocab"}
                newly_solved.append(t["id"])
                ref = sorted(t["train"], key=lambda e: len(e[0]))[0][0]
                _harvest_open(pool, prog, elite, ref)
            else:
                fbest = 0.0
                for f2, p2 in elite:
                    if CAND_TOKEN in p2 and f2 > fbest:
                        fbest = f2
                if fbest > best_f[t["id"]] - 0.05 and fbest > 0.0:
                    cand_pool.append((fbest, _copy_ir(ir), ti))
        cand_pool.sort(key=lambda e: (-e[0], canon(e[1]), e[2]))
        del cand_pool[CAND_POOL_CAP:]
        for ref_rec in refusals_gen:
            led.append("REFUSAL", dict(ref_rec, arm=arm, gen=g))

        # (4) Gate-IR A/B every gate_period generations
        if g % cfg["gate_period"] == 0:
            mut = mutate_gate(gtree, XorShift64Star(
                "gatemut:%d|%s|%s" % (g, arm, seed)))
            if gate_sha(mut) != gate_sha(gtree):
                inc_s, cand_s = 0, 0
                for ti, t in enumerate(tasks_d):
                    lbl = "gate_ab:%d:t%d|%s|%s" % (g, ti, arm, seed)
                    p1, e1, _ = search_task_open(
                        t, W, ops, B, XorShift64Star(lbl), gtree)
                    p2, e2, _ = search_task_open(
                        t, W, ops, B, XorShift64Star(lbl), mut)
                    gen_evals += e1 + e2
                    if solves_open(p1, ops, t):
                        inc_s += 1
                    if solves_open(p2, ops, t):
                        cand_s += 1
                accept = cand_s > inc_s
                led.append("GATE_AB", {
                    "arm": arm, "gen": g, "inc_solved": inc_s,
                    "cand_solved": cand_s, "accepted": bool(accept),
                    "inc_sha": gate_sha(gtree), "cand_sha": gate_sha(mut),
                    "cand_tree": mut if accept else None,
                })
                if accept:
                    gtree = mut

        # refit the base manifold from the harvest pool (ancestor's
        # fit_manifold convention; floor 1.0 everywhere -- G1)
        W = fit_manifold_open(pool, ops, gtree)

        # (5) FROZEN evaluation -- curve only, never fed back. Each
        # solve is ledgered as a permanent witness {task, program,
        # vocab sha at solve time} for the cumulative LEAP COUNT.
        frozen_ids = []
        frozen_witnesses = []
        for fi, t in enumerate(tasks_f):
            prng = XorShift64Star("frozen:g%d:t%d|%s|%s"
                                  % (g, fi, arm, seed))
            prog, ev_, _e = search_task_open(t, W, ops, B, prng, gtree)
            gen_evals += ev_
            if prog is not None and solves_open(prog, ops, t):
                frozen_ids.append(t["id"])
                frozen_witnesses.append([t["id"], list(prog),
                                         vocab_sha(ops)])
        frozen_curve.append(len(frozen_ids))

        # (6) ledger the generation
        evals_arm += gen_evals
        # every fresh stream is fully determined by its ledgered label;
        # opgen is the one long-lived stream, so its raw state is
        # recorded at each generation boundary
        led.append("GEN", {
            "arm": arm, "gen": g,
            "solved_discovery": len(solved),
            "newly_solved": sorted(newly_solved),
            "attempts": attempts,
            "admissions": list(admissions_gen),
            "n_screened": len(screened),
            "n_refusals": len(refusals_gen),
            "frozen_solved": len(frozen_ids),
            "frozen_ids": sorted(frozen_ids),
            "frozen_witnesses": sorted(frozen_witnesses),
            "vocab_sha": vocab_sha(ops),
            "vocab_size": len(ops),
            "gate_sha": gate_sha(gtree),
            "evals": gen_evals,
            "opgen_state": opgen.state,
            "streams": ["opgen|%s|%s" % (arm, seed),
                        "search:g%d:t*|%s|%s" % (g, arm, seed),
                        "cand:g%d:c*:t*|%s|%s" % (g, arm, seed),
                        "gate_ab:%d:t*|%s|%s" % (g, arm, seed),
                        "frozen:g%d:t*|%s|%s" % (g, arm, seed)],
        })
        if not quiet:
            print("  [%s] gen %2d: discovery %2d/%d  admissions %d "
                  "(vocab %d)  frozen %d/%d  evals %d"
                  % (arm, g, len(solved), len(tasks_d),
                     len(admissions_gen), len(ops), len(frozen_ids),
                     len(tasks_f), gen_evals))

        # stopping rule -- OPEN arm only: OPEN_OFF must run the exact
        # generation count it is given (compute parity with OPEN)
        if admissions_gen:
            stall = 0
        else:
            stall += 1
        flat = (len(frozen_curve) >= cfg["stall_gens"]
                and len(set(frozen_curve[-cfg["stall_gens"]:])) == 1)
        if admission_on and stall >= cfg["stall_gens"] and flat:
            stop_reason = "stall"
            break
    led.append("STOP", {"arm": arm, "gens_run": gens_run,
                        "reason": stop_reason,
                        "evals_arm": evals_arm})
    return {"arm": arm, "ops": ops, "gtree": gtree, "W": W,
            "solved": solved, "frozen_curve": frozen_curve,
            "gens_run": gens_run, "evals": evals_arm,
            "n_admissions": n_admissions, "stop_reason": stop_reason}


# ---------------------------------------------------------------------------
# EFFICIENCY PROBES -- seed-solvable tasks; speed deltas are reported on
# one line and are NOT evidence for this expedition's question.
# ---------------------------------------------------------------------------

EFF_PIPES = [["cumsum"], ["sort", "reverse"], ["double", "inc"],
             ["tail", "rotate"]]


def efficiency_probe(res_on, seed):
    B = CONFIG["budget"]
    tasks = []
    prng = XorShift64Star("eff|%s" % seed)
    for pipe in EFF_PIPES:
        t = None
        while t is None:
            t = make_task(pipe, prng)
        t["id"] = "e%02d" % len(tasks)
        tasks.append(t)
    W0 = uniform_manifold_open({})
    g0 = gen0_gate_tree()
    on_ev, on_s, off_ev, off_s = 0, 0, 0, 0
    for i, t in enumerate(tasks):
        lbl = "eff:t%d|%s" % (i, seed)
        p1, e1, _ = search_task_open(t, res_on["W"], res_on["ops"], B,
                                     XorShift64Star(lbl), res_on["gtree"])
        on_ev += e1
        if solves_open(p1, res_on["ops"], t):
            on_s += 1
        p2, e2, _ = search_task_open(t, W0, {}, B,
                                     XorShift64Star(lbl), g0)
        off_ev += e2
        if solves_open(p2, {}, t):
            off_s += 1
    return {"n_tasks": len(tasks), "open_solved": on_s,
            "open_evals": on_ev, "seed_solved": off_s,
            "seed_evals": off_ev}


# ---------------------------------------------------------------------------
# LEAP COUNT (cumulative, witness-based) -- derived from the LEDGER
# ONLY: the operator registry is reconstructed from ADMISSION IR, tasks
# from TASK records, witnesses from GEN records; nothing is read from
# live engine state and the run is never re-executed.
# ---------------------------------------------------------------------------

def tasks_from_ledger(led):
    out = {}
    for rec in led.find("TASK"):
        b = rec["body"]
        out[b["id"]] = {
            "id": b["id"], "split": b["split"], "pipe": list(b["pipe"]),
            "level": b["level"],
            "train": [(list(x), list(y)) for x, y in b["train"]],
            "test": [(list(x), list(y)) for x, y in b["test"]],
        }
    return out


def ops_from_ledger(led, arm="OPEN", up_to_gen=None):
    """Reconstruct the operator registry from ledgered ADMISSION IR;
    every entry is re-keyed and verified against T4 (op_sha =
    sha256(canon(IR)))."""
    ops = {}
    for rec in led.find("ADMISSION", arm=arm):
        b = rec["body"]
        if up_to_gen is not None and b["gen"] > up_to_gen:
            continue
        if op_sha(b["ir"]) != b["op_sha"]:
            sys.exit("WITNESS FAULT: ADMISSION %s IR does not hash to "
                     "its ledgered op_sha -- ledger corruption" % b["op"])
        ops[b["op"]] = {"ir": _copy_ir(b["ir"]), "sha": b["op_sha"]}
    return ops


def derive_witness_bfs(task, ops):
    """Legacy-ledger fallback: derive a witness program for a ledgered
    frozen solve by exhaustive breadth-first enumeration over the
    reconstructed vocabulary (depth <= MAX_DEPTH, deterministic order,
    dedup by full output vector over the task's train+test inputs --
    sound and complete, as in the C1 certifier). Returns the first
    exactly-solving pipeline, or None."""
    inputs = [x for x, _y in task["train"] + task["test"]]
    target = tuple(tuple(y) for _x, y in task["train"] + task["test"])
    toks = token_space_open(ops)
    base = tuple(tuple(_c(list(x))) for x in inputs)
    if base == target:
        return []
    seen = {base}
    frontier = [(base, [])]
    for _d in range(1, MAX_DEPTH + 1):
        nxt = []
        for outs, pipe in frontier:
            for tok in toks:
                cand = tuple(tuple(apply_token_open(list(o), tok, ops))
                             for o in outs)
                if cand in seen:
                    continue
                q = pipe + [tok]
                if cand == target:
                    return q
                seen.add(cand)
                nxt.append((cand, q))
        frontier = nxt
    return None


def derive_leaps(led, arm="OPEN"):
    """The XIX.1 headline: frozen tasks with >= 1 ledgered witness that
    re-executes exactly through the interpreter, registry rebuilt from
    ledgered IR. A witness that fails re-execution ABORTS (ledger
    corruption). Returns (leaps, legacy_final, n_frozen) where each
    leap is {task, first_gen, n_solve_gens, witness, op_shas}."""
    tasks = tasks_from_ledger(led)
    frozen_ids_all = sorted(t for t in tasks
                            if tasks[t]["split"] == "frozen")
    events = {}
    solve_gens = {}
    legacy_final = 0
    for rec in led.find("GEN", arm=arm):
        b = rec["body"]
        legacy_final = b["frozen_solved"]
        for tid in b["frozen_ids"]:
            solve_gens.setdefault(tid, []).append(b["gen"])
        if "frozen_witnesses" in b:
            for tid, prog, vsha in b["frozen_witnesses"]:
                events.setdefault(tid, []).append(
                    (b["gen"], list(prog), vsha))
        else:
            for tid in b["frozen_ids"]:
                events.setdefault(tid, []).append(
                    (b["gen"], None, b["vocab_sha"]))
    leaps = []
    for tid in sorted(events):
        evs = sorted(events[tid], key=lambda e: e[0])
        first_gen, prog, vsha = evs[0]
        task = tasks[tid]
        ops_at = ops_from_ledger(led, arm=arm, up_to_gen=first_gen)
        if prog is None:
            prog = derive_witness_bfs(task, ops_at)
            if prog is None:
                sys.exit("WITNESS FAULT: ledger records a frozen solve "
                         "of %s at gen %d but no witness exists at "
                         "depth <= %d over the vocabulary of that "
                         "generation -- ledger corruption"
                         % (tid, first_gen, MAX_DEPTH))
        full_ops = ops_from_ledger(led, arm=arm)
        for x, y in task["train"] + task["test"]:
            if run_tokens_open(prog, full_ops, x) != y:
                sys.exit("WITNESS FAULT: witness %s for frozen task %s "
                         "(gen %d) fails re-execution -- ledger "
                         "corruption; report aborted" % (prog, tid,
                                                         first_gen))
        used_shas = sorted({full_ops[tok]["sha"] for tok in prog
                            if tok in full_ops})
        leaps.append({"task": tid, "first_gen": first_gen,
                      "n_solve_gens": len(solve_gens.get(tid, [])),
                      "witness": list(prog), "vocab_sha": vsha,
                      "op_shas": used_shas})
    return leaps, legacy_final, len(frozen_ids_all)


def print_report_from_ledger(led):
    """The XIX.1 report, derived from ledger records only."""
    g = led.records[0]["body"]
    cfg = g["config"]
    csha = hashlib.sha256(canon(cfg).encode()).hexdigest()[:10]
    n_gens_off = len(led.find("GEN", arm="OPEN_OFF"))
    leaps, legacy_final, n_frozen = derive_leaps(led, arm="OPEN")
    off_gens = [r["body"]["frozen_solved"]
                for r in led.find("GEN", arm="OPEN_OFF")]
    off_cum = sum(off_gens)
    off_disc = 0
    for r in led.find("GEN", arm="OPEN_OFF"):
        off_disc = r["body"]["solved_discovery"]
    curve_on = [r["body"]["frozen_solved"]
                for r in led.find("GEN", arm="OPEN")]
    print("")
    print("=" * 72)
    print("LEAPFORGE-OPEN -- Expedition XIX report  (config %s, seed %s)"
          % (csha, g["seed"]))
    print("=" * 72)
    print("LEAP COUNT (cumulative, witness-verified): %d / %d"
          % (len(leaps), n_frozen))
    print("  A leap = a FROZEN task (all carry C1 inexpressibility")
    print("  certificates) with a ledgered witness program that")
    print("  re-executes exactly, registry rebuilt from ledgered IR.")
    print("  Zero is a publishable number.")
    for lp in leaps:
        print("  %s  first solve gen %2d   solved in %d/%d gens   "
              "witness %s" % (lp["task"], lp["first_gen"],
                              lp["n_solve_gens"], len(curve_on),
                              lp["witness"]))
        for sha in lp["op_shas"]:
            print("        admitting op sha %s" % sha[:16])
    print("final-generation sample (legacy XIX metric): %d / %d"
          % (legacy_final, n_frozen))
    print("frozen curve (OPEN):     %s" % curve_on)
    print("frozen curve (OPEN_OFF): %s" % off_gens)
    admissions = led.find("ADMISSION", arm="OPEN")
    print("")
    print("ADMISSION LINEAGE (%d admissions):" % len(admissions))
    for rec in admissions:
        b = rec["body"]
        print("  gen %2d  task %s (C1 %s...)" % (b["gen"],
              b["solved_task_id"], b["certificate_sha"][:12]))
        print("          -> %s = %s" % (b["op"], canon(b["ir"])))
        print("          vocab %s -> %s   program %s"
              % (b["parent_vocab_sha"], b["new_vocab_sha"],
                 b["program"]))
    if not admissions:
        print("  (none -- reported plainly, not softened)")
    print("")
    print("NULL DISCIPLINE: OPEN_OFF (admission disabled, same budgets, "
          "%d generations)" % n_gens_off)
    print("  certified frozen solves: cumulative %d, max/gen %d; "
          "certified discovery solves %d  (structural floor; must be "
          "0 by C1)" % (off_cum, max(off_gens) if off_gens else 0,
                        off_disc))
    if off_cum != 0 or off_disc != 0:
        sys.exit("CERTIFICATE BUG: OPEN_OFF shows certified solves in "
                 "the ledger; C1 forbids this. Abort.")
    for rec in led.find("EFFICIENCY"):
        e = rec["body"]
        print("")
        print("efficiency (not evidence): seed-solvable probes: open "
              "vocab %d/%d solved in %d evals vs seed-only %d/%d in %d "
              "evals" % (e["open_solved"], e["n_tasks"],
                         e["open_evals"], e["seed_solved"],
                         e["n_tasks"], e["seed_evals"]))
    for rec in led.find("REPORT"):
        b = rec["body"]
        print("")
        print("discovery solved (OPEN): %d/%d   admissions: %d   "
              "stop: %s" % (b["discovery_solved_open"],
                            b["n_discovery"], b["n_admissions"],
                            b["stop_open"]))
        print("evals: OPEN %d   OPEN_OFF %d  (budget-identical arms; "
              "actual usage reported)" % (b["evals_open"],
                                          b["evals_off"]))
        print("final vocab sha %s   gate sha %s"
              % (b["vocab_sha_final"], b["gate_sha_final"]))
    return leaps


# ---------------------------------------------------------------------------
# EXPEDITION -- ledger plumbing, the two arms, the report.
# ---------------------------------------------------------------------------

def cfg_sha():
    return hashlib.sha256(canon(CONFIG).encode()).hexdigest()[:10]


def ledger_path(seed):
    return os.path.join(CONFIG["outdir"],
                        "open_%s_s%s.jsonl" % (cfg_sha(), seed))


def expedition_core(seed, led, quiet=False):
    """The complete deterministic pipeline: GENESIS, XPRIM manifest,
    certified task generation, OPEN arm, OPEN_OFF arm, efficiency
    probe, REPORT record. Everything is a pure function of (source,
    CONFIG, seed); --replay re-simulates it bit-identically."""
    fp0 = substrate_fingerprint()
    led.append("GENESIS", {
        "config": dict(CONFIG), "seed": str(seed), "mission": MISSION,
        "source_sha": audit_sources(quiet=True)["source_sha"],
        "fingerprint": fp0,
    })
    led.append("XPRIMS", {
        "names": XNAMES,
        "behavior_shas": {
            nm: hashlib.sha256(canon(
                [list(XPRIMS[nm](list(p))) for p in PROBES])
                .encode()).hexdigest()[:16]
            for nm in XNAMES},
    })
    if not quiet:
        print("generating %d discovery + %d frozen certified tasks..."
              % (CONFIG["n_discovery"], CONFIG["n_frozen"]))
    tasks_d = gen_certified_tasks(CONFIG["n_discovery"],
                                  "taskgen|%s" % seed, "d",
                                  "discovery", led)
    tasks_f = gen_certified_tasks(CONFIG["n_frozen"],
                                  "frozen_taskgen|%s" % seed, "f",
                                  "frozen", led)
    if substrate_fingerprint() != fp0:
        sys.exit("SUBSTRATE FINGERPRINT DRIFT -- aborting")
    if not quiet:
        print("running OPEN arm (admission live)...")
    res_on = run_arm(tasks_d, tasks_f, CONFIG["generations"], True,
                     "OPEN", seed, led, quiet=quiet)
    if not quiet:
        print("running OPEN_OFF arm (admission disabled, same budgets, "
              "%d generations)..." % res_on["gens_run"])
    res_off = run_arm(tasks_d, tasks_f, res_on["gens_run"], False,
                      "OPEN_OFF", seed, led, quiet=quiet)
    eff = efficiency_probe(res_on, seed)
    led.append("EFFICIENCY", eff)
    off_final = res_off["frozen_curve"][-1] if res_off["frozen_curve"] \
        else 0
    # the abort condition covers EVERY generation, not just the final
    # point: any transient OPEN_OFF solve of a certified task is a
    # certificate bug
    off_any_frozen = max(res_off["frozen_curve"]) \
        if res_off["frozen_curve"] else 0
    off_disc = len(res_off["solved"])
    leaps, _legacy, _nf = derive_leaps(led, arm="OPEN")
    report_body = {
        "seed": str(seed),
        "leap_count_cumulative": len(leaps),
        "leaps": leaps,
        "leap_count": res_on["frozen_curve"][-1]
        if res_on["frozen_curve"] else 0,
        "n_frozen": len(tasks_f),
        "frozen_curve_open": list(res_on["frozen_curve"]),
        "frozen_curve_off": list(res_off["frozen_curve"]),
        "off_frozen_final": off_final,
        "off_frozen_max": off_any_frozen,
        "off_discovery_solved": off_disc,
        "n_admissions": res_on["n_admissions"],
        "discovery_solved_open": len(res_on["solved"]),
        "n_discovery": len(tasks_d),
        "vocab_final": [[nm, res_on["ops"][nm]["sha"]]
                        for nm in sorted(res_on["ops"])],
        "vocab_sha_final": vocab_sha(res_on["ops"]),
        "gate_sha_final": gate_sha(res_on["gtree"]),
        "evals_open": res_on["evals"],
        "evals_off": res_off["evals"],
        "stop_open": res_on["stop_reason"],
        "efficiency": eff,
    }
    led.append("REPORT", report_body)
    if off_any_frozen != 0 or off_disc != 0:
        sys.exit("CERTIFICATE BUG: OPEN_OFF solved certified tasks "
                 "(max frozen/gen %d, discovery %d); C1 forbids this. "
                 "Abort -- fix the certifier before any claim."
                 % (off_any_frozen, off_disc))
    return report_body, res_on, res_off, tasks_d, tasks_f


def expedition(seed):
    audit_sources(quiet=True)
    if not os.path.isdir(CONFIG["outdir"]):
        os.makedirs(CONFIG["outdir"])
    path = ledger_path(seed)
    if os.path.exists(path):
        sys.exit("ledger %s already exists -- one unit per (config, "
                 "seed); use --replay or remove it first" % path)
    led = Ledger(path)
    expedition_core(seed, led)
    print_report_from_ledger(led)
    led.verify()
    print("\nledger verified -> %s" % path)
    print("replay: python3 %s --replay %s"
          % (os.path.basename(__file__), path))


# ---------------------------------------------------------------------------
# REPLAY -- re-simulate a recorded run; every record must match.
# ---------------------------------------------------------------------------

def replay(path):
    led = Ledger(path)
    if not led.records:
        sys.exit("no ledger at %s" % path)
    led.verify()
    g = led.records[0]["body"]
    CONFIG.clear()
    CONFIG.update(g["config"])
    cur = audit_sources(quiet=True)["source_sha"]
    sha_ok = (g["source_sha"] == cur)
    if not sha_ok:
        print("WARNING: source sha differs from GENESIS -- code identity "
              "NOT proven")
    mem = Ledger(None)
    expedition_core(g["seed"], mem, quiet=True)
    if len(mem.records) != len(led.records):
        sys.exit("REPLAY FAIL: record count %d != %d"
                 % (len(mem.records), len(led.records)))
    n_bit = 0
    for i, (a, b) in enumerate(zip(mem.records, led.records)):
        if a["kind"] != b["kind"]:
            sys.exit("REPLAY FAIL: record %d kind %s != %s"
                     % (i, a["kind"], b["kind"]))
        ba, bb = dict(a["body"]), dict(b["body"])
        if i == 0 and not sha_ok:
            ba.__setitem__("source_sha", "MASKED")
            bb.__setitem__("source_sha", "MASKED")
        if canon(ba) != canon(bb):
            sys.exit("REPLAY FAIL: record %d (%s) body differs"
                     % (i, a["kind"]))
        if a["hash"] == b["hash"]:
            n_bit += 1
    if sha_ok and n_bit == len(led.records):
        print("REPLAY VERIFIED: %d records re-simulated bit-identically "
              "(hash chain included)" % len(led.records))
    else:
        print("REPLAY VERIFIED: %d record bodies match (%d hashes "
              "bit-identical; source sha %s)"
              % (len(led.records), n_bit,
                 "match" if sha_ok else "DIFFERS"))
    return 0


# ---------------------------------------------------------------------------
# SELFTEST -- permanent honesty suite (ships in the file).
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


def _fuzz_lists(prng, n, maxlen=12):
    out = []
    for _ in range(n):
        length = prng.below(maxlen + 1)
        out.append([prng.below(256) for _i in range(length)])
    return out


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
        assert set(rep["imports"]) <= ALLOWED_MODULES
    ok.append(_t("source audit passes (imports/eval/line-cap/claims)", t03))

    def t04():
        assert substrate_fingerprint() == ANCESTOR_FINGERPRINT, \
            "seed substrate drifted from the ancestor"
        assert len(NAMES) == 20
        _seen, levels = build(max_depth=2)
        assert len(levels[1]) == 20 and len(levels[2]) == 294
        seen2, counts2, _sha = enum_battery(PROBES, 2)
        assert counts2 == {1: 20, 2: 294}, \
            "extended enumerator disagrees with ancestor build()"
        assert len(seen2) == 1 + 20 + 294
    ok.append(_t("substrate verbatim; enumerators agree (20/294)", t04))

    def t05():
        # T1 totality + T2 determinism over >= 10,000 DISTINCT random
        # lists (fresh lists per operator draw)
        gen = XorShift64Star("t05gen")
        fz = XorShift64Star("t05fuzz")
        n_lists = 0
        for _ in range(260):
            ir = grow_op(gen)
            assert check_op(ir), "grower produced invalid IR"
            for xs in _fuzz_lists(fz, 40):
                o1 = apply_ir(ir, xs)
                o2 = apply_ir(ir, list(xs))
                n_lists += 1
                assert o1 == o2, "T2 determinism broken"
                assert len(o1) <= MAXLEN
                assert all(isinstance(v, int) and 0 <= v <= 255
                           for v in o1), "byte clamp broken"
        assert n_lists >= 10000, "fuzz volume too small: %d" % n_lists
        # the grower is budget-safe by construction: sweep every budget
        for b in range(1, MAX_IR_NODES + 1):
            for _ in range(150):
                ir = grow_op(gen, b)
                assert ir_nodes(ir) <= b, \
                    "grow_op(%d) returned %d nodes" % (b, ir_nodes(ir))
    ok.append(_t("T1/T2: interpreter total + deterministic (10k+ fuzz)",
                 t05))

    def t06():
        # T3 cost cap: the cap mechanism collapses to []
        ir = ["MAP", ["ADD", ["V"], ["C", 1]]]
        big = list(range(20))
        assert apply_ir(ir, big) == [v + 1 for v in big]
        assert apply_ir(ir, big, cap=5) == [], \
            "cost-cap collapse to [] broken"
        assert apply_ir(["SLICE", 0, 24, 1], big, cap=3) == []
        # grammar admits no recursion: cost of any capped tree is finite
        # and bounded by COST_CAP by construction
        gen = XorShift64Star("t06")
        for _ in range(50):
            ir2 = grow_op(gen)
            assert isinstance(apply_ir(ir2, big), list)
    ok.append(_t("T3: cost cap collapses to [] (gate-0 convention)", t06))

    def t07():
        a = ["MAP", ["MUL", ["V"], ["V"]]]
        b = ["MAP", ["MUL", ["V"], ["C", 3]]]
        assert op_sha(a) == op_sha(["MAP", ["MUL", ["V"], ["V"]]])
        assert op_sha(a) != op_sha(b)
        assert op_sha(a) == hashlib.sha256(canon(a).encode()).hexdigest()
    ok.append(_t("T4: op_sha = sha256(canon(IR)), stable + distinct",
                 t07))

    def t08():
        g0 = gen0_gate_tree()
        assert check_gate(g0)
        for p in PROBES:
            assert classify(g0, p) == get_state_context(p)
        prng = XorShift64Star("t08fuzz")
        n = 0
        for xs in _fuzz_lists(prng, 10000, maxlen=10):
            a = classify(g0, xs)
            b = get_state_context(xs)
            assert a == b, "gen-0 gate differs on %s: %d != %d" \
                % (xs, a, b)
            assert 0 <= a < NUM_GATES_OPEN
            n += 1
        assert n >= 10000
        assert classify(g0, []) == 0 and classify(g0, [5]) == 0
        assert classify(g0, [1, 2, 3]) == 1
        assert classify(g0, [7, 9, 8]) == 2
        assert classify(g0, [0, 255, 0]) == 3
    ok.append(_t("generation-0 gate == ancestor gate (10k fuzz)", t08))

    def t09():
        ops = {}
        W = uniform_manifold_open(ops)
        assert manifold_min(W) == 1.0
        assert len(W) == NUM_GATES_OPEN
        scored = [(1.0, ["inc", "cumsum"], [3, 1, 4]),
                  (0.8, ["sort", "sort"], [5, 5])]
        W1 = fit_manifold_open(scored, ops, gen0_gate_tree())
        ops2 = {"o01": {"ir": ["MAP", ["MUL", ["V"], ["V"]]],
                        "sha": op_sha(["MAP", ["MUL", ["V"], ["V"]]])}}
        W2 = grow_manifold_open(W1, ops2)
        assert manifold_min(W2) >= 1.0, "G1 floor broken by growth"
        for gk in W2:
            assert "o01" in W2[gk], "op row missing in slice %s" % gk
            for r in W2[gk]:
                assert "o01" in W2[gk][r], "op column missing"
        h = manifold_row_entropy(fit_manifold_open(
            [(1.0, ["cumsum", "reverse"], [3, 1, 4])] * 30, ops,
            gen0_gate_tree()))
        assert h >= 1.5, "entropy collapsed to %.3f bits" % h
    ok.append(_t("G1 floor after grow_manifold on synthetic admission",
                 t09))

    def t10():
        prng = XorShift64Star("t10")
        t = None
        while t is None:
            t = make_task_open(["square"], prng)
        c1 = certify_c1(t)
        assert c1 is not None, "certifier rejected a known XPRIM task"
        assert c1["n_behaviors"] > 50000
        t2 = None
        while t2 is None:
            t2 = make_task(["inc"], prng)
        t2["pipe"] = ["inc"]
        assert certify_c1(t2) is None, \
            "certifier accepted a seed-solvable task"
        t3 = None
        while t3 is None:
            t3 = make_task(["cumsum", "reverse"], prng)
        assert certify_c1(t3) is None, \
            "certifier accepted a depth-2 seed task"
    ok.append(_t("C1: rejects seed-solvable, accepts XPRIM task", t10))

    def t11():
        wit = _xprim_witnesses()
        wit2 = _xprim_witnesses()
        assert canon(wit) == canon(wit2)
        assert sorted(wit) == XNAMES
        prng = XorShift64Star("t11fuzz")
        lists = _fuzz_lists(prng, 200)
        for nm in XNAMES:
            ir = wit[nm]
            assert check_op(ir), "witness %s invalid or > %d nodes" \
                % (nm, MAX_IR_NODES)
            for xs in lists:
                assert apply_ir(ir, xs) == XPRIMS[nm](list(xs)), \
                    "witness %s diverges from XPRIM on %s" % (nm, xs)
            s = sig_ir(ir)
            for snm in NAMES:
                assert s != sig([snm]), \
                    "XPRIM %s behaviorally equals seed %s" % (nm, snm)
            assert s != IDENT
    ok.append(_t("C2: witnesses valid, total, equal to XPRIMS, novel",
                 t11))

    def t12():
        # witness ISOLATION: (a) no module global contains a witness
        # tree; (b) AST proof: _xprim_witnesses is called only from
        # certify_c2 and selftest; (c) empty initial registries.
        wit_canons = set()
        for v in _xprim_witnesses().values():
            wit_canons.add(canon(v))

        def safe_canon(obj):
            try:
                return canon(obj)
            except TypeError:
                return None

        def contains_witness(obj):
            if isinstance(obj, list):
                if safe_canon(obj) in wit_canons:
                    return True
                return any(contains_witness(ch) for ch in obj)
            if isinstance(obj, tuple):
                return any(contains_witness(ch) for ch in obj)
            if isinstance(obj, dict):
                return any(contains_witness(ch) for ch in obj.values())
            return False
        for gname, gval in sorted(globals().items()):
            if gname == "_xprim_witnesses":
                continue
            assert not contains_witness(gval), \
                "witness tree leaked into global %s" % gname
        tree = ast.parse(_self_source())
        callers = set()
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Call) \
                            and isinstance(sub.func, ast.Name) \
                            and sub.func.id == "_xprim_witnesses":
                        callers.add(node.name)
            else:
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Call) \
                            and isinstance(sub.func, ast.Name) \
                            and sub.func.id == "_xprim_witnesses":
                        callers.add("<module>")
        assert callers <= {"_xprim_witnesses", "certify_c2", "selftest"}, \
            "witness table reachable from: %s" % sorted(callers)
        # registry inspection: a fresh proposal batch (empty pool, no
        # near-miss data) shares no sha with the witness table -- and
        # being stream-deterministic, this holds on every run
        opgen = XorShift64Star("opgen|ISO|0")
        screened = propose_ops(opgen, [], [0], 50, {})
        wshas = {op_sha(v) for v in _xprim_witnesses().values()}
        assert not any(sha in wshas for _ir, sha, _ti in screened), \
            "raw proposal stream reproduced a witness sha"
        assert propose_ops(XorShift64Star("x"), [], [], 10, {}) == []
    ok.append(_t("C2 isolation: witnesses unreachable from proposals",
                 t12))

    def t13():
        gen = XorShift64Star("t13")
        # a candidate behaviorally equal to seed "inc" must be screened
        # out; a genuinely novel one must survive
        inc_ir = ["MAP", ["ADD", ["V"], ["C", 1]]]
        assert sig_ir(inc_ir) == sig(["inc"])
        sq_ir = ["MAP", ["MUL", ["V"], ["V"]]]
        known = _seed_sigs()
        assert sig_ir(sq_ir) not in known
        pool = [(0.9, inc_ir, 0), (0.9, sq_ir, 0)]
        found_dup = False
        screened = propose_ops(gen, pool, [0], 200, {})
        for ir, _sha, _ti in screened:
            assert sig_ir(ir) not in known, "duplicate survived screen"
            if canon(ir) == canon(inc_ir):
                found_dup = True
        assert not found_dup
    ok.append(_t("screening: seed-equivalent behaviour discarded", t13))

    def t14():
        # admission end-to-end on a synthetic certified task: the
        # square op solves it; manifold grows; lineage fields present
        CONFIG.update({"pop_size": 16, "budget": 600,
                       "k_proposals": 10, "pool_keep": 24})
        prng = XorShift64Star("t14")
        t = None
        while t is None:
            t = make_task_open(["square"], prng)
        t["id"] = "dXX"
        c1 = certify_c1(t)
        assert c1 is not None
        t["c1"] = c1
        ops_plus = {CAND_TOKEN: {"ir": ["MAP", ["MUL", ["V"], ["V"]]],
                                 "sha": op_sha(["MAP", ["MUL", ["V"],
                                                        ["V"]]])}}
        W = grow_manifold_open(uniform_manifold_open({}), ops_plus)
        # stream "t14|s" finds a train-exact program that fails the
        # held-out test set -- solves_open must REJECT that one
        prog_s, _ev, _el = search_task_open(t, W, ops_plus, 600,
                                            XorShift64Star("t14|s"),
                                            gen0_gate_tree())
        assert prog_s is not None
        assert check_exact_open(prog_s, ops_plus, t["train"])
        assert not solves_open(prog_s, ops_plus, t), \
            "generalization check failed to reject a train-only match"
        prog, _ev, _el = search_task_open(t, W, ops_plus, 600,
                                          XorShift64Star("t14|a"),
                                          gen0_gate_tree())
        assert prog == [CAND_TOKEN], \
            "square candidate failed to solve its own task"
        assert solves_open(prog, ops_plus, t)
        CONFIG.clear()
        CONFIG.update(cfg_backup)
    ok.append(_t("admission mechanics: candidate op solves C1 task",
                 t14))

    def t15():
        # replay determinism: a tiny 2-generation run, twice, in-memory
        CONFIG.clear()
        CONFIG.update(CONFIG_SMOKE)
        CONFIG.update({"n_discovery": 2, "n_frozen": 1, "budget": 150,
                       "generations": 2, "k_proposals": 8,
                       "pop_size": 12})
        led1 = Ledger(None)
        rep1, _a, _b, _c, _d = expedition_core("t15", led1, quiet=True)
        led2 = Ledger(None)
        rep2, _a2, _b2, _c2, _d2 = expedition_core("t15", led2,
                                                   quiet=True)
        assert len(led1.records) == len(led2.records)
        for r1, r2 in zip(led1.records, led2.records):
            assert r1["hash"] == r2["hash"], \
                "replay divergence in %s record" % r1["kind"]
        assert canon(rep1) == canon(rep2)
        assert rep1["off_frozen_final"] == 0
        assert rep1["off_discovery_solved"] == 0
        assert led1.verify() is True
        CONFIG.clear()
        CONFIG.update(cfg_backup)
    ok.append(_t("replay: 2-gen run re-simulates bit-identically", t15))

    def t16():
        # frozen isolation: frozen evaluation is a pure read -- the
        # search mutates only its local manifold copy
        prng = XorShift64Star("t16")
        t = None
        while t is None:
            t = make_task_open(["mirror"], prng)
        W = uniform_manifold_open({})
        before = canon(_round(W))
        _p, _e, _el = search_task_open(t, W, {}, 200,
                                       XorShift64Star("t16|s"),
                                       gen0_gate_tree())
        assert canon(_round(W)) == before, \
            "search mutated the shared base manifold"
    ok.append(_t("frozen discipline: eval leaves engine state untouched",
                 t16))

    def t17():
        g0 = gen0_gate_tree()
        prng = XorShift64Star("t17")
        for _ in range(300):
            m = mutate_gate(g0, prng)
            assert check_gate(m), "gate mutation produced invalid tree"
            for xs in ([], [1], [3, 1, 4], [200, 200, 0, 5]):
                gid = classify(m, xs)
                assert 0 <= gid < NUM_GATES_OPEN
        assert gate_sha(g0) == gate_sha(gen0_gate_tree())
    ok.append(_t("gate mutations stay valid, total, in-range", t17))

    def t18():
        # cumulative witness-based LEAP COUNT (the XIX.1 metric)
        prng = XorShift64Star("t18")
        tsq = None
        while tsq is None:
            tsq = make_task_open(["square"], prng)
        ttr = None
        while ttr is None:
            ttr = make_task_open(["triple"], prng)
        sq = ["MAP", ["MUL", ["V"], ["V"]]]
        tr3 = ["MAP", ["MUL", ["V"], ["C", 3]]]

        def task_rec(tid, t):
            return {"id": tid, "split": "frozen", "pipe": t["pipe"],
                    "level": t["level"],
                    "train": [[list(x), list(y)] for x, y in t["train"]],
                    "test": [[list(x), list(y)] for x, y in t["test"]]}

        def adm_rec(name, ir, gen):
            return {"arm": "OPEN", "gen": gen, "op": name,
                    "op_sha": op_sha(ir), "ir": ir,
                    "solved_task_id": "dSY", "certificate_sha": "c",
                    "parent_vocab_sha": "p", "new_vocab_sha": "n",
                    "program": [name]}

        def gen_rec(gen, wits, ids):
            return {"arm": "OPEN", "gen": gen, "solved_discovery": 0,
                    "frozen_solved": len(ids), "frozen_ids": ids,
                    "frozen_witnesses": wits, "vocab_sha": "v"}

        # (a) one valid witness -> LEAP COUNT 1
        led = Ledger(None)
        led.append("TASK", task_rec("fS0", tsq))
        led.append("ADMISSION", adm_rec("o01", sq, 1))
        led.append("GEN", gen_rec(1, [["fS0", ["o01"], "v"]], ["fS0"]))
        leaps, legacy, nf = derive_leaps(led)
        assert len(leaps) == 1 and nf == 1 and legacy == 1
        assert leaps[0]["task"] == "fS0" and leaps[0]["witness"] == \
            ["o01"] and leaps[0]["first_gen"] == 1
        # (b) corrupted witness program -> WITNESS FAULT abort
        led_b = Ledger(None)
        led_b.append("TASK", task_rec("fS0", tsq))
        led_b.append("ADMISSION", adm_rec("o01", sq, 1))
        led_b.append("GEN", gen_rec(1, [["fS0", ["o01", "inc"], "v"]],
                                    ["fS0"]))
        aborted = False
        try:
            derive_leaps(led_b)
        except SystemExit:
            aborted = True
        assert aborted, "corrupted witness did not abort the report"
        # (c) cumulative semantics: an early-only solve and a
        # final-only solve each count exactly once; a task solved in
        # several generations still counts once
        led_c = Ledger(None)
        led_c.append("TASK", task_rec("fS0", tsq))
        led_c.append("TASK", task_rec("fS1", ttr))
        led_c.append("ADMISSION", adm_rec("o01", sq, 1))
        led_c.append("ADMISSION", adm_rec("o02", tr3, 1))
        led_c.append("GEN", gen_rec(1, [["fS0", ["o01"], "v"]], ["fS0"]))
        led_c.append("GEN", gen_rec(2, [["fS0", ["o01"], "v"]], ["fS0"]))
        led_c.append("GEN", gen_rec(3, [["fS1", ["o02"], "v"]], ["fS1"]))
        leaps_c, legacy_c, nf_c = derive_leaps(led_c)
        assert len(leaps_c) == 2 and nf_c == 2
        by = {lp["task"]: lp for lp in leaps_c}
        assert by["fS0"]["n_solve_gens"] == 2
        assert by["fS0"]["first_gen"] == 1
        assert by["fS1"]["n_solve_gens"] == 1
        assert legacy_c == 1, "legacy metric must be the final sample"
        # legacy-format ledger (no frozen_witnesses field): the witness
        # is derived by exhaustive BFS over the ledgered vocabulary
        led_d = Ledger(None)
        led_d.append("TASK", task_rec("fS0", tsq))
        led_d.append("ADMISSION", adm_rec("o01", sq, 1))
        led_d.append("GEN", {"arm": "OPEN", "gen": 1,
                             "solved_discovery": 0, "frozen_solved": 1,
                             "frozen_ids": ["fS0"], "vocab_sha": "v"})
        leaps_d, _lg, _nf = derive_leaps(led_d)
        assert len(leaps_d) == 1 and leaps_d[0]["witness"] == ["o01"], \
            "legacy BFS derivation failed: %s" % leaps_d
    ok.append(_t("leap count: cumulative witness semantics + faults",
                 t18))

    CONFIG.clear()
    CONFIG.update(cfg_backup)
    n_pass = sum(1 for x in ok if x)
    print("\n%d/%d tests passed" % (n_pass, len(ok)))
    if n_pass != len(ok):
        sys.exit(1)
    print("ALL TESTS PASS")


def _round(o):
    if isinstance(o, dict):
        return {k: _round(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_round(v) for v in o]
    if isinstance(o, float):
        return round(o, 9)
    return o


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    argv = sys.argv[1:]
    if not argv:
        print(__doc__)
        return
    if "--selftest" in argv:
        audit_sources(quiet=True)
        selftest()
        return
    if "--audit" in argv:
        audit_sources()
        return
    if "--replay" in argv:
        path = argv[argv.index("--replay") + 1]
        replay(path)
        return
    if "--report" in argv:
        path = argv[argv.index("--report") + 1]
        led = Ledger(path)
        if not led.records:
            sys.exit("no ledger at %s" % path)
        led.verify()
        print_report_from_ledger(led)
        return
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
        seed = "1"
        if "--seed" in argv:
            seed = argv[argv.index("--seed") + 1]
        expedition(seed)
        return
    sys.exit("unknown arguments: %s (try --selftest, --audit, "
             "--profile smoke|full, --replay <ledger>, "
             "--report <ledger>)" % argv)


if __name__ == "__main__":
    main()

# end of file -- leapforge_open.py (xix)
