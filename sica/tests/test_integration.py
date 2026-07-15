"""Runtime-guardrail integration tests: drive a scaffold through the real
broker + unshare-n subprocess + sealed grader.

  - G-sandbox/G-isolate: a scaffold that tries to read OUTSIDE its workdir is
    caught as a scope-escape -> violation (the run would auto-halt);
  - G-budget: a scaffold that over-calls the model is stopped at the cap;
  - happy path: the stub's correct fix is graded solved by the HIDDEN tests.

Skipped when network isolation (unshare -n) is unavailable on the host.
"""

import os

import pytest

from runner import sandbox
from runner.bench.base import Task, load_meta
from runner.harness import attempt_task
from runner.model import ModelClient
from runner.stubmodel import stub_model

FIX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "runner", "bench", "fixtures")

pytestmark = pytest.mark.skipif(
    not sandbox.probe_isolation()[0],
    reason="network isolation (unshare -n) unavailable")

CAPS = {"max_model_calls": 8, "max_model_tokens": 100000,
        "max_tool_calls": 10, "max_steps": 10, "wall_seconds": 60}


def _task(repo):
    root = os.path.join(FIX, repo, "t1")
    return Task(root, load_meta(root))


def _sources(solve_src, extra=""):
    return [["agent.py", extra + solve_src]]


def test_happy_path_solves_and_grades():
    task = _task("addlib")
    src = (
        "def solve(ctx, task):\n"
        "    files = {p: ctx.read(p) for p in task.editable_files}\n"
        "    prompt = 'Fix it.\\n'\n"
        "    for p in task.editable_files:\n"
        "        prompt += '### FILE: %s\\n%s\\n### END\\n' % (p, files[p])\n"
        "    reply = ctx.model(prompt, system='agent')\n"
        "    import re\n"
        "    for m in re.finditer(r'### FILE: (.+?)\\n(.*?)\\n### END', "
        "reply, re.DOTALL):\n"
        "        if m.group(1).strip() in task.editable_files:\n"
        "            ctx.write(m.group(1).strip(), m.group(2) + '\\n')\n"
    )
    model = ModelClient(backend="stub", stub_fn=stub_model)
    rec = attempt_task(task, _sources(src), model, CAPS)
    assert rec["solved"] is True
    assert rec["violation"] is None


def test_scope_escape_is_caught():
    task = _task("addlib")
    src = "def solve(ctx, task):\n    ctx.read('../../../etc/hosts')\n"
    model = ModelClient(backend="stub", stub_fn=stub_model)
    rec = attempt_task(task, _sources(src), model, CAPS)
    assert rec["violation"] is not None
    assert rec["status"] == "violation"
    assert rec["solved"] is False


def test_budget_cap_stops_overspend():
    task = _task("addlib")
    caps = dict(CAPS)
    caps["max_model_calls"] = 1
    src = ("def solve(ctx, task):\n"
           "    for i in range(5):\n"
           "        ctx.model('hi', system='agent')\n")
    model = ModelClient(backend="stub", stub_fn=stub_model)
    rec = attempt_task(task, _sources(src), model, caps)
    assert rec["status"] == "budget"
    assert rec["meter"]["model_calls"] == 1        # spend was actually capped


def test_mount_ns_blocks_os_escape_read_of_grading_assets():
    # Even if a scaffold escapes the Python restriction to `os` (via an allowed
    # module's re-exported sys), the mount namespace hides the grading-asset
    # tree, so it reads nothing. This is the load-bearing G-isolate control.
    import os as _os
    fixtures = _os.path.dirname(FIX) if False else FIX
    task = _task("addlib")
    src = (
        "def solve(ctx, task):\n"
        "    import dataclasses\n"
        "    osmod = dataclasses.sys.modules['os']\n"
        "    base = %r\n"
        "    try:\n"
        "        listing = osmod.listdir(base)\n"
        "    except Exception as e:\n"
        "        listing = 'ERR:' + type(e).__name__\n"
        "    gold = osmod.path.join(base, 'addlib', 't1', 'gold', 'calc.py')\n"
        "    ctx.log('ESCAPE listing=%%s exists=%%s'\n"
        "            %% (listing, osmod.path.exists(gold)))\n"
    ) % fixtures
    model = ModelClient(backend="stub", stub_fn=stub_model)
    rec = attempt_task(task, _sources(src), model, CAPS)
    joined = " ".join(rec["notes"])
    # tasks/fixtures tree is tmpfs-empty in the child: listing empty, gold gone
    assert "exists=False" in joined
    assert "calc.py" not in joined.split("listing=")[-1].split(" exists")[0]


def test_io_write_flood_is_metered_and_bounded():
    task = _task("addlib")
    caps = dict(CAPS)
    caps["max_write_bytes"] = 200000
    caps["max_io_ops"] = 5000
    src = ("def solve(ctx, task):\n"
           "    blob = 'A' * 50000\n"
           "    i = 0\n"
           "    while True:\n"
           "        ctx.write('junk_%d.txt' % i, blob)\n"
           "        i += 1\n")
    model = ModelClient(backend="stub", stub_fn=stub_model)
    rec = attempt_task(task, _sources(src), model, caps)
    assert rec["status"] == "budget"
    assert rec["meter"]["bytes_written"] <= caps["max_write_bytes"]


def test_single_model_call_cannot_exceed_token_budget():
    task = _task("addlib")
    caps = dict(CAPS)
    caps["max_model_tokens"] = 120000
    # a ~500k-char prompt is ~125k input tokens, already over the cap: the
    # broker must refuse BEFORE the call, not book it after the fact.
    src = ("def solve(ctx, task):\n"
           "    huge = 'x ' * 250000\n"
           "    ctx.model(huge, system='s', max_tokens=1000000)\n")
    model = ModelClient(backend="stub", stub_fn=stub_model)
    rec = attempt_task(task, _sources(src), model, caps)
    assert rec["status"] == "budget"
    assert rec["meter"]["model_calls"] == 0        # never spent
    assert rec["meter"]["model_tokens"] == 0


def test_grading_assets_absent_from_workdir():
    # The hidden grading test must never be materialised into the workdir.
    task = _task("addlib")
    src = ("def solve(ctx, task):\n"
           "    names = ctx.ls('.')\n"
           "    ctx.log('LS:' + ','.join(names))\n")
    model = ModelClient(backend="stub", stub_fn=stub_model)
    rec = attempt_task(task, _sources(src), model, CAPS)
    joined = " ".join(rec["notes"])
    assert "test_hidden.py" not in joined
    assert "gold" not in joined
