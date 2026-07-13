"""Static-guardrail unit tests: the audit (G-isolate/G-sandbox compile-time),
restricted builtins, meters (G-budget), and the ledger's tamper detection."""

import pytest

from runner import audit, restricted
from runner.meters import Meter, BudgetError
from runner.ledger import Ledger, record_hash


# --------------------------------------------------------------- audit
def test_audit_accepts_clean_scaffold():
    src = "import json\nimport re\n\ndef solve(ctx, task):\n    return 1\n"
    rep = audit.audit_source(src)
    assert rep["ok"]


@pytest.mark.parametrize("bad", [
    "import os\n",
    "import subprocess\n",
    "from pathlib import Path\n",
    "open('/etc/passwd')\n",
    "eval('1+1')\n",
    "exec('x=1')\n",
    "x = ().__class__\n",
    "y = obj.__globals__\n",
    "__import__('os')\n",
    "z = getattr(o, 'a')\n",
    "c = compile('1','<s>','eval')\n",
])
def test_audit_rejects_escapes(bad):
    with pytest.raises(audit.AuditError):
        audit.audit_source("def solve(ctx, task):\n    pass\n" + bad)


# --------------------------------------------------- restricted namespace
def test_restricted_builtins_have_no_dangerous_names():
    b = restricted.safe_builtins()
    for name in ("open", "eval", "exec", "compile", "globals", "getattr",
                 "setattr", "input", "vars", "memoryview"):
        assert name not in b
    assert "__import__" in b and callable(b["__import__"])


def test_guarded_import_blocks_os():
    with pytest.raises(ImportError):
        restricted.guarded_import("os")
    # allowed stdlib still imports
    assert restricted.guarded_import("json") is not None


def test_dry_load_rejects_forbidden_import_at_module_level():
    # audit is separate; here we prove the restricted exec itself blocks it
    ok, err, _ = restricted.dry_load([["m.py", "import socket\n"]])
    assert not ok and "socket" in err


def test_dry_load_requires_solve():
    ok, err, has = restricted.dry_load([["m.py", "x = 1\n"]])
    assert not ok and not has


# ------------------------------------------------------------- meters
def test_meter_caps_block_before_spend():
    caps = {"max_model_calls": 2, "max_model_tokens": 1000,
            "max_tool_calls": 1, "max_steps": 1, "wall_seconds": 100}
    t = [0.0]
    m = Meter(caps, clock=lambda: t[0])
    m.check_model(); m.record_model(10, 10, 0.0)
    m.check_model(); m.record_model(10, 10, 0.0)
    with pytest.raises(BudgetError):
        m.check_model()                       # 3rd call blocked


def test_meter_wall_clock():
    caps = {"max_model_calls": 99, "max_model_tokens": 10**9,
            "max_tool_calls": 99, "max_steps": 99, "wall_seconds": 5}
    t = [0.0]
    m = Meter(caps, clock=lambda: t[0])
    m.check_step()
    t[0] = 6.0
    with pytest.raises(BudgetError):
        m.check_step()


# ------------------------------------------------------------- ledger
def test_ledger_tamper_detected(tmp_path):
    p = str(tmp_path / "l.jsonl")
    led = Ledger(p)
    led.append("A", {"x": 1})
    led.append("B", {"y": 2})
    # tamper with the stored body
    lines = open(p).read().splitlines()
    import json
    rec = json.loads(lines[0])
    rec["body"]["x"] = 999
    lines[0] = json.dumps(rec)
    open(p, "w").write("\n".join(lines) + "\n")
    with pytest.raises(ValueError):
        Ledger(p)


def test_ledger_hash_chain():
    led = Ledger(None)
    h1 = led.append("A", {"n": 1})
    h2 = led.append("A", {"n": 2})
    assert h1 != h2
    assert led.records[1]["prev"] == h1
    assert record_hash(h1, {"n": 2}) == h2
