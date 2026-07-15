#!/usr/bin/env python3
"""External-benchmark TRANSFER read on REAL SWE-bench Verified instances,
without the official Docker harness (docker is unavailable here).

For each instance we: clone the real repo at base_commit, pip-install its deps,
run a SICA scaffold on the buggy repo (issue = the real GitHub problem
statement; editable files = the files the gold patch touches), then GRADE by
applying the real hidden test_patch and running the real FAIL_TO_PASS /
PASS_TO_PASS tests. The agent never sees test_patch (applied only in the sealed
eval copy) -- G-isolate holds against tests we did NOT author.

This answers the open-ended question the synthetic axes cannot: do the earned
leaps lift the solve rate on real issues, graded by real hidden tests?

Modes:
  selftest <instance_id>            -- $0: confirm baseline FAIL_TO_PASS fails and
                                       the gold patch makes it pass (plumbing check)
  run <scaffold_dir> <ids...>       -- run one scaffold over instances, grade, report
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runner import config, sandbox, scaffold_io           # noqa: E402
from runner.broker import Broker                           # noqa: E402
from runner.meters import Meter                            # noqa: E402
from runner.model import ModelClient                       # noqa: E402

CACHE = "/home/user/LeapForge-Gated-VM/sica/.swebench_cache"
REPO_URL = {"psf/requests": "https://github.com/psf/requests.git",
            "pallets/flask": "https://github.com/pallets/flask.git",
            "pylint-dev/pylint": "https://github.com/pylint-dev/pylint.git",
            "pytest-dev/pytest": "https://github.com/pytest-dev/pytest.git"}
# Option 3: the target repo is NEVER `pip install -e .`'d (that would run its
# setup.py unsandboxed). Instead the repo is made importable via PYTHONPATH
# (import root below), its third-party deps are installed as trusted PyPI
# WHEELS (no arbitrary code at install), and its own code executes ONLY inside
# the net-namespaced run_test_command sandbox.
IMPORT_ROOT = {"psf/requests": "", "pallets/flask": "src",
               "pylint-dev/pylint": "", "pytest-dev/pytest": "src"}
DEPS = {
    "psf/requests": ["pytest", "urllib3", "idna", "certifi",
                     "charset-normalizer", "chardet"],
    "pallets/flask": ["pytest", "werkzeug", "jinja2", "click", "itsdangerous",
                      "markupsafe", "blinker"],
    "pylint-dev/pylint": ["pytest", "astroid", "isort", "mccabe",
                          "platformdirs", "tomlkit", "dill"],
}


def _run(cmd, cwd=None, timeout=600, env=None):
    return subprocess.run(cmd, cwd=cwd, timeout=timeout,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          env=env)


def load_instances(ids):
    from datasets import load_dataset
    ds = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
    by_id = {x["instance_id"]: x for x in ds}
    return [by_id[i] for i in ids]


def editable_files(patch):
    out = []
    for ln in patch.splitlines():
        if ln.startswith("+++ b/"):
            p = ln[6:].strip()
            low = p.lower()
            if "test" in low or low.endswith("conftest.py"):
                continue
            out.append(p)
    return out


def prepare(inst):
    """Clone at base_commit (fetch only) + install trusted PyPI dep WHEELS.
    The target repo's own setup.py is never run on the host."""
    iid = inst["instance_id"]
    base = os.path.join(CACHE, iid)
    if not os.path.isdir(os.path.join(base, ".git")):
        if not os.path.isdir(CACHE):
            os.makedirs(CACHE)
        url = REPO_URL[inst["repo"]]
        r = _run(["git", "clone", "--quiet", url, base], timeout=600)
        if r.returncode != 0:
            raise RuntimeError("clone failed: %s"
                               % r.stdout[-400:].decode("utf-8", "replace"))
        _run(["git", "checkout", "-q", inst["base_commit"]], cwd=base)
    # third-party deps as WHEELS only (no source builds -> no arbitrary code).
    deps = DEPS.get(inst["repo"], ["pytest"])
    _run([sys.executable, "-m", "pip", "install", "-q", "--only-binary=:all:"]
         + deps, timeout=900)
    return base


def _import_root(base, repo):
    sub = IMPORT_ROOT.get(repo, "")
    return os.path.join(base, sub) if sub else base


def _copytree(src, dst, with_git=False):
    ig = shutil.ignore_patterns("__pycache__", "*.pyc",
                                *([] if with_git else [".git"]))
    shutil.copytree(src, dst, ignore=ig, symlinks=True)


def _pytest_nodes(evaldir, nodes, pythonpath, timeout=300):
    if not nodes:
        return {"ok": True, "rc": 0, "empty": True}
    argv = [sys.executable, "-m", "pytest", "-p", "no:cacheprovider",
            "-q", "--no-header", "-o", "addopts="] + list(nodes)
    # external repo code executes ONLY here: net-namespaced sandbox, with the
    # eval copy on PYTHONPATH so `import <pkg>` resolves to the code under test.
    r = sandbox.run_test_command(argv, evaldir, timeout=timeout,
                                 env_extra={"PYTHONPATH": pythonpath})
    return {"ok": r.code == 0, "rc": r.code, "empty": False,
            "tail": (r.stdout or "")[-1200:]}


def grade(base, inst, agent_workdir=None, p2p_cap=15, timeout=400):
    """Sealed grade: eval = base + test_patch + (agent edits). Returns dict."""
    tmp = tempfile.mkdtemp(prefix="swe-grade-")
    evaldir = os.path.join(tmp, "eval")
    try:
        _copytree(base, evaldir, with_git=True)
        pp = _import_root(evaldir, inst["repo"])
        # apply the hidden test patch
        pf = os.path.join(tmp, "test.patch")
        with open(pf, "w", encoding="utf-8") as f:
            f.write(inst["test_patch"])
        ap = _run(["git", "apply", "--whitespace=nowarn", pf], cwd=evaldir)
        if ap.returncode != 0:
            ap = _run(["git", "apply", "--3way", "--whitespace=nowarn", pf],
                      cwd=evaldir)
        if ap.returncode != 0:
            return {"error": "test_patch apply failed: %s"
                    % ap.stdout[-300:].decode("utf-8", "replace")}
        # overlay the agent's edits to editable files (source only)
        if agent_workdir is not None:
            for rel in editable_files(inst["patch"]):
                src = os.path.join(agent_workdir, rel)
                dst = os.path.join(evaldir, rel)
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
        f2p = json.loads(inst["FAIL_TO_PASS"]) if isinstance(
            inst["FAIL_TO_PASS"], str) else inst["FAIL_TO_PASS"]
        p2p = json.loads(inst["PASS_TO_PASS"]) if isinstance(
            inst["PASS_TO_PASS"], str) else inst["PASS_TO_PASS"]
        r_f2p = _pytest_nodes(evaldir, f2p, pp, timeout)
        r_p2p = _pytest_nodes(evaldir, p2p[:p2p_cap], pp, timeout)
        return {"f2p_ok": r_f2p["ok"], "p2p_ok": r_p2p["ok"],
                "f2p_rc": r_f2p.get("rc"), "p2p_rc": r_p2p.get("rc"),
                "solved": bool(r_f2p["ok"] and r_p2p["ok"]),
                "n_f2p": len(f2p), "n_p2p_run": min(len(p2p), p2p_cap),
                "tail": r_f2p.get("tail", "")}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_agent(scaffold, inst, base, model, caps):
    tmp = tempfile.mkdtemp(prefix="swe-agent-")
    workdir = os.path.join(tmp, "work")
    try:
        _copytree(base, workdir, with_git=False)
        ed = editable_files(inst["patch"])
        public = {"name": inst["instance_id"],
                  "issue": inst["problem_statement"][:6000],
                  "editable_files": ed, "files": ed, "test_command": []}
        meter = Meter(caps)
        broker = Broker(workdir, public, meter, model,
                        public_test_paths=["__sica_no_public_tests__.py"],
                        logger=lambda *a: None)
        bres = broker.run(scaffold_io.scaffold_sources(scaffold))
        g = grade(base, inst, agent_workdir=workdir)
        return {"status": bres.status, "meter": meter.snapshot(),
                "editable": ed, **g}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main(argv):
    if len(argv) >= 3 and argv[1] == "selftest":
        sandbox.require_isolation()
        inst = load_instances([argv[2]])[0]
        print("prepare", inst["instance_id"], inst["repo"], "...")
        base = prepare(inst)
        print("editable:", editable_files(inst["patch"]))
        b = grade(base, inst, agent_workdir=None)
        print("BASELINE (no fix): f2p_ok=%s (want False)  p2p_ok=%s (want True)  %s"
              % (b.get("f2p_ok"), b.get("p2p_ok"), b.get("error", "")))
        # gold: apply gold patch to a workdir, then grade
        tmp = tempfile.mkdtemp(); wd = os.path.join(tmp, "gold")
        _copytree(base, wd)
        pf = os.path.join(tmp, "gold.patch"); open(pf, "w").write(inst["patch"])
        _run(["git", "init", "-q"], cwd=wd); _run(["git", "apply", "--whitespace=nowarn", pf], cwd=wd)
        g = grade(base, inst, agent_workdir=wd)
        print("GOLD PATCH: f2p_ok=%s (want True)  p2p_ok=%s (want True)  solved=%s"
              % (g.get("f2p_ok"), g.get("p2p_ok"), g.get("solved")))
        shutil.rmtree(tmp, ignore_errors=True)
        ok = (b.get("f2p_ok") is False and g.get("solved") is True)
        print("PLUMBING", "OK" if ok else "BROKEN")
        return 0 if ok else 1

    if argv[1] == "run":
        scaffold_dir = argv[2]; ids = argv[3:]
        scaffold = scaffold_io.load_scaffold(scaffold_dir)
        label = scaffold["manifest"].get("scaffold_version", scaffold_dir)
        sandbox.require_isolation()
        cfg = config.make_config("smoke", "claude_cli", "swe")
        caps = dict(cfg["task_budget"]); caps["wall_seconds"] = 300
        model = ModelClient(backend="claude_cli", model=cfg["model_pinned"])
        insts = load_instances(ids)
        rows = []
        for inst in insts:
            base = prepare(inst)
            res = run_agent(scaffold, inst, base, model, caps)
            rows.append({"id": inst["instance_id"], **{k: res.get(k) for k in
                        ("solved", "f2p_ok", "p2p_ok", "status")}})
            print("  %-34s solved=%s (f2p=%s p2p=%s status=%s)"
                  % (inst["instance_id"], res.get("solved"), res.get("f2p_ok"),
                     res.get("p2p_ok"), res.get("status")), flush=True)
        solved = sum(1 for r in rows if r["solved"])
        print("SCAFFOLD %s : %d/%d solved  cost=$%.4f"
              % (label, solved, len(rows), model.session_totals()["cost_usd"]))
        out = os.path.join(config.RUNS_DIR, "swebench_%s.json"
                           % scaffold_io.scaffold_sha(scaffold))
        json.dump({"label": label, "rows": rows, "solved": solved,
                   "n": len(rows), "cost": model.session_totals()["cost_usd"]},
                  open(out, "w"), indent=2)
        print("->", out)
        return 0
    print("usage: swebench_transfer.py selftest <id> | run <scaffold_dir> <ids...>")
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
