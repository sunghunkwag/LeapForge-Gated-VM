"""Static audit of scaffold code (the compile-time half of G-isolate and
G-sandbox).

The scaffold is model-authored, self-modifying code. Before any candidate
scaffold is executed it must pass this audit. The audit is defence-in-depth:
the *runtime* guarantees come from running the scaffold in a no-network
subprocess with a restricted builtins namespace where every capability is
brokered through `ctx` (see broker.py / sandbox.py). But we refuse to even
launch a scaffold that statically tries to:

  - import anything outside a tiny stdlib allowlist (no os, sys, subprocess,
    socket, importlib, pathlib, shutil, ctypes, builtins, ...);
  - call eval / exec / compile / __import__ / open / globals / vars / getattr
    / setattr on dynamic names;
  - touch dunder attributes (__class__, __globals__, __subclasses__, ...) --
    the classic Python sandbox-escape gadget chain;
  - read or write files by any means other than the ctx API.

Grading assets (hidden fail-to-pass tests, gold patches) live OUTSIDE every
path the scaffold can name, and the ctx file API is confined to the task
workdir, so even a scaffold that passed a buggy audit could not read them.
This module makes that structural guarantee also a static one.
"""

import ast

# Modules a scaffold module may import. Deliberately tiny and IO-free.
ALLOWED_IMPORTS = {
    "json", "re", "math", "difflib", "collections", "itertools",
    "functools", "heapq", "string", "textwrap", "dataclasses", "typing",
    "hashlib", "bisect", "copy",
}

FORBIDDEN_CALLS = {
    "eval", "exec", "compile", "__import__", "open", "globals", "vars",
    "getattr", "setattr", "delattr", "input", "breakpoint", "memoryview",
    "classmethod", "staticmethod",
}

# Attribute access to any of these names (or any dunder) is refused.
# Beyond the classic dunder gadgets, we also deny the names by which an allowed
# stdlib module re-exports a dangerous module as a PLAIN attribute (e.g.
# `dataclasses.builtins`, `typing.sys`, `<mod>.sys.modules['os']`). This is
# defence-in-depth; the load-bearing containment is the mount namespace that
# hides grading assets from the child even if it reaches os.
FORBIDDEN_ATTRS = {
    "__class__", "__bases__", "__mro__", "__subclasses__", "__globals__",
    "__code__", "__builtins__", "__dict__", "__getattribute__", "__reduce__",
    "__reduce_ex__", "__import__", "__loader__", "__spec__", "func_globals",
    "gi_frame", "cr_frame", "f_globals", "f_builtins", "f_locals",
    # module-bridge names
    "sys", "os", "builtins", "modules", "subprocess", "importlib", "ctypes",
    "socket", "posix", "nt", "inspect", "pty", "runpy", "pdb",
    "system", "popen", "execv", "execve", "execvp", "spawn", "spawnv",
    "fork", "fdopen",
}


class AuditError(Exception):
    pass


def audit_source(src, filename="<scaffold>"):
    """Raise AuditError on any violation; return a small report on success."""
    try:
        tree = ast.parse(src, filename=filename)
    except SyntaxError as e:
        raise AuditError("%s: syntax error: %s" % (filename, e))

    imports = set()
    violations = []

    for node in ast.walk(tree):
        # imports
        if isinstance(node, ast.Import):
            for a in node.names:
                top = a.name.split(".")[0]
                imports.add(top)
                if top not in ALLOWED_IMPORTS:
                    violations.append("import '%s' (line %d)"
                                      % (a.name, node.lineno))
        elif isinstance(node, ast.ImportFrom):
            top = (node.module or "").split(".")[0]
            imports.add(top)
            if node.level and node.level > 0:
                # relative import within the scaffold package is allowed
                pass
            elif top not in ALLOWED_IMPORTS:
                violations.append("from '%s' import (line %d)"
                                  % (node.module, node.lineno))
        # forbidden calls by bare name
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_CALLS:
                violations.append("call to '%s' (line %d)"
                                  % (node.func.id, node.lineno))
        # forbidden / dunder attribute access
        elif isinstance(node, ast.Attribute):
            attr = node.attr
            if attr in FORBIDDEN_ATTRS or (attr.startswith("__")
                                           and attr.endswith("__")):
                violations.append("attribute '%s' (line %d)"
                                  % (attr, node.lineno))
        # names that are dunder gadgets
        elif isinstance(node, ast.Name):
            if node.id in ("__builtins__", "__import__", "__loader__"):
                violations.append("name '%s' (line %d)"
                                  % (node.id, node.lineno))

    if violations:
        raise AuditError("%s: %s" % (filename, "; ".join(violations)))

    return {"imports": sorted(imports), "ok": True}


def audit_scaffold_files(files):
    """files: {relpath: source}. Audits each; raises on first violation."""
    reports = {}
    for rel, src in sorted(files.items()):
        if not rel.endswith(".py"):
            continue
        reports[rel] = audit_source(src, filename=rel)
    return reports
