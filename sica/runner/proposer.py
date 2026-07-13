"""Failure-driven, memory-informed, K-candidate scaffold proposer
(directive sections 1.1, 1.2, 1.3, 1.5).

After a generation, the incumbent's own FAILING TRAIN transcripts and the
heldout-stripped improvement memory are shown to the model, which proposes a
single highest-leverage change to the scaffold -- targeting a failure MODE seen
repeatedly, with a rationale and an expected-effect prediction. K such
proposals are made, each steered toward a different failure mode, to form the
tournament field. The model may rewrite prompts, the loop, the policy knobs,
OR add a whole new tool file (section 1.5).

Every candidate is:
  - parsed from the model's JSON,
  - applied to the incumbent (scaffold_io.apply_edits),
  - statically audited (audit.py: no os/open/eval/dunder escapes),
  - dry-loaded in the restricted namespace (must define solve()).
A candidate that fails any check is dropped with its reason logged; it never
reaches the gate.
"""

import json
import re

from . import audit, restricted, scaffold_io

CTX_API_DOC = """\
The scaffold runs sandboxed. It may ONLY act through the `ctx` object:
  ctx.model(prompt, system=None, max_tokens=2048) -> str   (one model call)
  ctx.read(path) -> str|None      ctx.write(path, content)
  ctx.ls(path='.') -> [names]     ctx.grep(pattern, path='.', max_hits=200)
  ctx.run_tests(paths=None, timeout=60) -> {code,passed,failed,errors,stdout}
  ctx.log(msg)                    ctx.step()   (advances the metered step count)
  ctx.task.issue, ctx.task.editable_files, ctx.task.files, ctx.task.test_command
Hard constraints on scaffold code (a violation makes the candidate INELIGIBLE):
  - the ONLY imports allowed are: %s
  - NO os, sys, subprocess, open, eval, exec, compile, __import__, getattr,
    setattr, or any __dunder__ attribute access;
  - files in exec_order share ONE namespace (no importing each other);
  - you MUST keep a working solve(ctx, task) defined;
  - grading uses HIDDEN tests you cannot see; ctx.run_tests runs only the
    PUBLIC tests. Do not try to read or write anything outside the task.
""" % ", ".join(sorted(audit.ALLOWED_IMPORTS))

PROPOSER_SYSTEM = (
    "You are a research engineer improving a sandboxed coding agent's scaffold "
    "(its prompts, its plan/act/verify loop, its retry policy, and its tools). "
    "You change the scaffold to make it solve MORE held-out tasks. You target "
    "a specific, recurring failure mode with one high-leverage change and you "
    "predict its effect. You output ONLY a single JSON object."
)

_JSON = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json(text):
    t = text.strip()
    if t.startswith("```"):
        nl = t.find("\n")
        if nl != -1:
            t = t[nl + 1:]
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    try:
        return json.loads(t)
    except ValueError:
        m = _JSON.search(t)
        if m:
            try:
                return json.loads(m.group(0))
            except ValueError:
                return None
    return None


def _current_scaffold_text(scaffold):
    parts = []
    for name in scaffold["manifest"]["exec_order"]:
        parts.append("### FILE: %s\n%s\n### END\n"
                     % (name, scaffold["files"][name]))
    return "".join(parts)


def _build_prompt(scaffold, failure_digest, memory_view, steer, train_score,
                  n_train):
    j = json.dumps
    return "".join([
        "The current scaffold solved %d/%d TRAIN tasks. Here it is:\n\n"
        % (round(train_score * n_train), n_train),
        _current_scaffold_text(scaffold),
        "\n\nFailing TRAIN transcripts (heldout is NOT shown -- never optimise "
        "for it):\n", j(failure_digest, indent=1),
        "\n\nWhat past changes did/didn't pay off (train deltas only):\n",
        j(memory_view, indent=1),
        "\n\n", CTX_API_DOC,
        "\n\nFocus this proposal on the failure mode: %s\n" % steer,
        "\nReturn ONE JSON object with these keys:\n"
        '  "targeted_failure_mode": short string\n'
        '  "rationale": why this change addresses that mode\n'
        '  "predicted_effect": your expected train solve-rate change\n'
        '  "label": short kebab-case name for this scaffold\n'
        '  "files": {"<name.py>": "<FULL new contents>", ...}  '
        "(only files you change or ADD)\n"
        '  "exec_order": [ ... ]  (include ONLY if you add/reorder files)\n'
        "Include the ENTIRE contents of any file you touch. Keep solve(ctx, "
        "task) working. Output only the JSON object.",
    ])


# A rotating set of failure-mode steers so K candidates diversify (section 1.2).
DEFAULT_STEERS = [
    "the agent never inspects the failing test output before editing",
    "the agent edits without gathering enough surrounding code context",
    "the agent gives up too early / does not backtrack after a failed attempt",
    "the agent misformats its patch so no edit is applied",
    "the agent changes too much and breaks passing behaviour",
    "the agent does not localise WHICH function is wrong before editing",
    "the agent wastes budget re-reading instead of adding a reusable tool",
]


def _steers_for(failure_digest, k, prng):
    """Prefer steers grounded in the observed failures, then fill from the
    default pool; deterministic given the engine PRNG."""
    grounded = []
    statuses = [f.get("status") for f in failure_digest]
    if any(s == "budget" for s in statuses):
        grounded.append("the agent exhausts its token/step budget before "
                        "converging -- make it more economical")
    if any((f.get("error") or "").strip() for f in failure_digest):
        grounded.append("the agent hits errors it does not recover from")
    pool = grounded + list(DEFAULT_STEERS)
    prng.shuffle(pool)
    out = []
    i = 0
    while len(out) < k:
        out.append(pool[i % len(pool)])
        i += 1
    return out[:k]


def propose_candidate(model_client, scaffold, failure_digest, memory_view,
                      steer, train_score, n_train):
    """Make ONE candidate. Returns (candidate|None, info)."""
    prompt = _build_prompt(scaffold, failure_digest, memory_view, steer,
                           train_score, n_train)
    info = {"steer": steer}
    try:
        text, usage = model_client.complete(PROPOSER_SYSTEM, prompt,
                                            max_tokens=6000)
    except Exception as e:  # noqa
        info["error"] = "model error: %s" % e
        return None, info
    info["proposer_usage"] = usage
    obj = _extract_json(text)
    if not obj or not isinstance(obj.get("files"), dict) or not obj["files"]:
        info["error"] = "no usable JSON/files in proposal"
        return None, info
    info["targeted_failure_mode"] = obj.get("targeted_failure_mode", steer)
    info["rationale"] = str(obj.get("rationale", ""))[:600]
    info["predicted_effect"] = str(obj.get("predicted_effect", ""))[:300]
    info["label"] = str(obj.get("label", "child"))[:40]
    try:
        cand = scaffold_io.apply_edits(scaffold, {
            "files": obj["files"],
            "exec_order": obj.get("exec_order"),
            "label": info["label"],
        })
    except ValueError as e:
        info["error"] = "bad edits: %s" % e
        return None, info
    try:
        scaffold_io.audit_scaffold(cand)
    except audit.AuditError as e:
        info["error"] = "audit rejected: %s" % e
        return None, info
    ok, err, _has = restricted.dry_load(scaffold_io.scaffold_sources(cand))
    if not ok:
        info["error"] = "dry-load failed: %s" % err
        return None, info
    info["sha"] = scaffold_io.scaffold_sha(cand)
    return cand, info
