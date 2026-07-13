"""The restricted execution namespace for scaffold code.

Shared by the subprocess bootstrap (scaffold_runner.py, where the scaffold
actually runs against a live ctx) and by the proposer's dry-loader (which
checks a candidate defines solve() and loads cleanly, without any ctx or IO).
Scaffold code sees only safe builtins and a guarded __import__ that admits
nothing outside the stdlib allowlist.
"""

from .audit import ALLOWED_IMPORTS

_SAFE_BUILTIN_NAMES = [
    "True", "False", "None", "NotImplemented", "Ellipsis",
    "abs", "all", "any", "ascii", "bin", "bool", "bytearray", "bytes",
    "callable", "chr", "dict", "divmod", "enumerate", "filter", "float",
    "format", "frozenset", "hash", "hex", "int", "isinstance", "issubclass",
    "iter", "len", "list", "map", "max", "min", "next", "object", "oct",
    "ord", "pow", "print", "range", "repr", "reversed", "round", "set",
    "slice", "sorted", "str", "sum", "tuple", "zip",
    "Exception", "BaseException", "ValueError", "KeyError", "IndexError",
    "TypeError", "RuntimeError", "StopIteration", "AttributeError",
    "NotImplementedError", "ZeroDivisionError", "ArithmeticError",
    "AssertionError", "LookupError", "OverflowError", "FloatingPointError",
]


def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
    if level and level > 0:
        raise ImportError("relative imports are not permitted in scaffold code")
    top = name.split(".")[0]
    if top not in ALLOWED_IMPORTS:
        raise ImportError("import of %r is not permitted in scaffold code"
                          % name)
    return __import__(name, globals, locals, fromlist, level)


def safe_builtins():
    real = __builtins__ if isinstance(__builtins__, dict) else vars(__builtins__)
    b = {}
    for nm in _SAFE_BUILTIN_NAMES:
        if nm in real:
            b[nm] = real[nm]
    b["__import__"] = guarded_import
    return b


def dry_load(sources):
    """Exec scaffold sources in a fresh restricted namespace (no ctx, no IO).
    Returns (ok, error, has_solve). Module-level code that tries forbidden IO
    fails here, before the candidate ever reaches the gate."""
    ns = {"__builtins__": safe_builtins(), "__name__": "scaffold"}
    try:
        for name, src in sources:
            code = compile(src, "scaffold/%s" % name, "exec")
            exec(code, ns)  # noqa: S102 -- restricted namespace, audited source
    except Exception as e:  # noqa
        return False, "%s: %s" % (type(e).__name__, e), False
    solve = ns.get("solve")
    return callable(solve), (None if callable(solve) else "no solve()"), \
        callable(solve)
