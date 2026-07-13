"""Deterministic, offline stub model for $0 end-to-end engine verification.

It plays BOTH roles the engine needs:
  * as the AGENT model, it reads the editable file blocks out of the prompt and
    applies a small fixed set of corrections -- solving the fixture tasks whose
    bug it knows, and (crucially) solving the `hintbug` fixture ONLY when the
    prompt contains the token USE_SPECIAL_CASE;
  * as the PROPOSER model, it emits a valid candidate scaffold JSON that adds
    USE_SPECIAL_CASE to the scaffold's prompt rules -- so the candidate solves
    one more train task than the incumbent and is genuinely ADOPTED by the gate.

That closed loop lets `verify` exercise the real selection operator (tie ->
incumbent AND strict-winner adoption), memory, archive, and the curve, without
any network or spend. It is used ONLY by the verify profile; real runs use the
claude_cli backend and never touch this file.
"""

import re

_BLOCK = re.compile(r"###\s*FILE:\s*([^\n]+?)\s*\n(.*?)\n###\s*END", re.DOTALL)

# (old, new) corrections the stub agent knows how to make.
_FIXES = [
    ("return a - b", "return a + b"),
    ("total = total - v", "total = total + v"),
    ("result = x * 0", "result = x * 1"),
]
_SPECIAL_OLD = "return 0  # SPECIAL"
_SPECIAL_NEW = "return n * n  # SPECIAL"

PROPOSER_MARK = "research engineer improving"


def stub_model(system, prompt):
    if PROPOSER_MARK in (system or ""):
        return _stub_proposer(prompt)
    return _stub_agent(prompt)


def _stub_agent(prompt):
    use_special = "USE_SPECIAL_CASE" in prompt
    blocks = _BLOCK.findall(prompt)
    # The FIRST group of blocks in the prompt are the editable files (they
    # appear under "Current contents of the editable files"). Emit corrected
    # versions of any file we can fix.
    out = []
    seen = set()
    for path, body in blocks:
        path = path.strip().strip("`")
        if path in seen or path.endswith(".md"):
            continue
        seen.add(path)
        new = body
        for old, rep in _FIXES:
            new = new.replace(old, rep)
        if use_special:
            new = new.replace(_SPECIAL_OLD, _SPECIAL_NEW)
        if new != body:
            out.append("### FILE: %s\n%s\n### END" % (path, new))
    if not out:
        # nothing to fix that we recognise -> emit nothing parseable
        return "No change."
    return "\n".join(out)


# A self-contained, known-good replacement prompts.py that injects the
# USE_SPECIAL_CASE token into every built prompt. Hardcoded (rather than parsed
# from the proposer prompt) so it is robust and always audits + dry-loads.
_IMPROVED_PROMPTS = '''\
SYSTEM_PROMPT = (
    "You are an expert Python engineer. Fix the bug so the tests pass. "
    "Handle every branch, including the SPECIAL case."
)

FORMAT_RULES = (
    "Reply with complete file blocks marked FILE: <path> ... then the file. "
    "USE_SPECIAL_CASE: always handle the SPECIAL-case branch."
)


def _clip(text, limit):
    if text is None:
        return "(missing)"
    if len(text) <= limit:
        return text
    return text[:limit] + "\\n... [truncated] ..."


def build_fix_prompt(task, files, allowed, history, test_feedback, extra=""):
    parts = ["Issue:\\n", task.issue, "\\nYou may edit: ", ", ".join(allowed),
             "\\nUSE_SPECIAL_CASE: handle the SPECIAL case.\\n"]
    for path in allowed:
        parts.append("### FILE: %s\\n%s\\n### END\\n"
                     % (path, _clip(files.get(path), 8000)))
    if test_feedback:
        parts.append("\\nTests:\\n%s\\n" % test_feedback)
    if history:
        parts.append("\\nFeedback:\\n%s\\n" % history[-1])
    parts.append("\\n" + FORMAT_RULES)
    return "".join(parts)
'''


def _stub_proposer(prompt):
    import json
    obj = {
        "targeted_failure_mode": "agent ignores the SPECIAL-case branch",
        "rationale": "Inject an explicit SPECIAL-case instruction into the "
                     "prompt so the agent handles the branch it was silently "
                     "skipping.",
        "predicted_effect": "+train tasks solved (the SPECIAL-case fixtures)",
        "label": "add-special-hint",
        "files": {"prompts.py": _IMPROVED_PROMPTS},
    }
    return json.dumps(obj)
