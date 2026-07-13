# GEN0 tools, composed only from ctx primitives. New tools (symbol index,
# focused test runner, diff minimiser) are meant to be added here by the
# engine -- each is just a function over ctx.read/ls/grep/run_tests/model.

import re

_FILE_BLOCK = re.compile(
    r"###\s*FILE:\s*(?P<path>[^\n]+?)\s*\n(?P<body>.*?)\n###\s*END",
    re.DOTALL)


def strip_fences(text):
    t = text.strip()
    if t.startswith("```"):
        nl = t.find("\n")
        if nl != -1:
            t = t[nl + 1:]
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    return t


def parse_patch(text, allowed):
    """Extract {relpath: full_content} from model output, restricted to the
    allowed editable files. Returns {} if nothing parseable."""
    allowed_set = set(allowed)
    out = {}
    for m in _FILE_BLOCK.finditer(text or ""):
        path = m.group("path").strip().strip("`").strip()
        body = strip_fences(m.group("body"))
        if path in allowed_set:
            out[path] = body
    return out


def read_editable(ctx, task):
    files = {}
    for path in task.editable_files:
        files[path] = ctx.read(path)
    return files


def apply_patch(ctx, patch, allowed):
    allowed_set = set(allowed)
    n = 0
    for path, body in patch.items():
        if path in allowed_set and body is not None:
            ctx.write(path, body if body.endswith("\n") else body + "\n")
            n += 1
    return n


def summarize_tests(result):
    if result is None:
        return "(no test result)"
    if result.get("timed_out"):
        return "tests TIMED OUT"
    tail = (result.get("stdout") or "")[-1200:]
    return ("exit=%s passed=%s failed=%s errors=%s\n%s"
            % (result.get("code"), result.get("passed"),
               result.get("failed"), result.get("errors"), tail))


def tests_green(result):
    return (result is not None and not result.get("timed_out")
            and result.get("code") == 0 and result.get("failed", 0) == 0
            and result.get("errors", 0) == 0
            and result.get("passed", 0) > 0)


def gather_context(ctx, task):
    """Optional: pull a little extra repo context by searching for the
    editable files' base names. Cheap, best-effort, capped."""
    if not GREP_CONTEXT:
        return ""
    seen = []
    for path in task.editable_files:
        stem = path.split("/")[-1].split(".")[0]
        try:
            hits = ctx.grep(r"\b%s\b" % re.escape(stem), ".", 20)
        except Exception:
            hits = []
        for h in hits[:5]:
            line = "%s:%s: %s" % (h.get("path"), h.get("line"), h.get("text"))
            if line not in seen:
                seen.append(line)
    return "\n".join(seen[:40])
