# GEN0 prompts. Shares the scaffold namespace; may reference policy globals.

SYSTEM_PROMPT = (
    "You are an expert Python software engineer. You fix a bug in a small "
    "repository so that its tests pass. You are precise and you change as "
    "little as necessary. You ALWAYS reply using the exact file-block format "
    "you are asked for and nothing else."
)

FORMAT_RULES = (
    "Reply with the COMPLETE new contents of every file you change, each in a "
    "block delimited exactly like this:\n"
    "### FILE: <relative/path.py>\n"
    "<full file contents>\n"
    "### END\n"
    "Rules: only edit files from the allowed list; include the ENTIRE file, "
    "not a diff or a snippet; do not add commentary outside the blocks."
)


def _clip(text, limit):
    if text is None:
        return "(missing)"
    if len(text) <= limit:
        return text
    return text[:limit] + "\n... [truncated] ..."


def build_fix_prompt(task, files, allowed, history, test_feedback, extra=""):
    parts = []
    parts.append("A repository has a bug described by this issue:\n")
    parts.append(task.issue.strip() or "(no issue text)")
    parts.append("\n\nYou may edit ONLY these files: %s" % ", ".join(allowed))
    budget = MAX_CONTEXT_CHARS
    parts.append("\n\nCurrent contents of the editable files:\n")
    for path in allowed:
        body = files.get(path)
        share = max(800, budget // max(1, len(allowed)))
        parts.append("\n### FILE: %s\n%s\n### END\n" % (path, _clip(body, share)))
    if extra:
        parts.append("\nAdditional repository context:\n%s\n" % extra)
    if test_feedback:
        parts.append("\nWhen the current code is run against the visible "
                     "tests, the result is:\n%s\n" % test_feedback)
    if history:
        parts.append("\nYour previous attempt did not make the tests pass. "
                     "Feedback:\n%s\n" % history[-1])
    parts.append("\n" + FORMAT_RULES)
    return "".join(parts)
