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
    """Pull repository context by finding function definitions and constants.
    Extracts function names mentioned in the issue and searches the repo to show
    where those functions are defined and where constants are. Also includes
    helpers.py if present, as it typically documents the correct values."""
    if not GREP_CONTEXT:
        return ""
    
    issue_text = task.issue or ""
    seen = []
    
    # Extract function names mentioned in the issue (pattern: identifier followed by parentheses)
    func_names = re.findall(r'\b([a-zA-Z_]\w*)\s*\(', issue_text)
    func_names = list(dict.fromkeys(func_names))  # Deduplicate while preserving order
    
    # Search for definitions of these functions to show where the bug is located
    for func_name in func_names[:4]:
        try:
            pattern = r'def\s+' + re.escape(func_name) + r'\s*\('
            hits = ctx.grep(pattern, ".", 20)
            for h in hits[:1]:  # Just first match per function
                line = "%s:%s: %s" % (h.get("path"), h.get("line"), h.get("text"))
                if line not in seen:
                    seen.append(line)
        except Exception:
            pass
    
    # Include helpers.py if it exists, as issues often reference its docstring/comments
    # for the correct values needed to fix the bug
    try:
        helpers_content = ctx.read("helpers.py")
        if helpers_content:
            seen.append("\n--- helpers.py (has correct values) ---")
            # Include first 2000 chars (typically covers module docstring and key comments)
            if len(helpers_content) > 2000:
                seen.append(helpers_content[:2000] + "\n... [truncated] ...")
            else:
                seen.append(helpers_content)
    except Exception:
        pass
    
    # Search for constant/mapping definitions (ALL_CAPS naming convention).
    # These typically represent the 'correct values' or config referenced in the issue.
    try:
        hits = ctx.grep(r'\b[A-Z_]{2,}\s*=', ".", 30)
        for h in hits[:15]:
            text = (h.get("text") or "").strip()
            if len(text) < 150:  # Skip very long lines
                line = "%s:%s: %s" % (h.get("path"), h.get("line"), text)
                if line not in seen:
                    seen.append(line)
    except Exception:
        pass
    
    return "\n".join(seen)
