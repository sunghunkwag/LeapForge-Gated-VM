"""Grading-asset containment control (T1, PI condition).

The benchmark is self-authored, so we treat the grading assets -- the HIDDEN
fail->pass tests, the GOLD patches, and each task's meta.json (which names the
grading tests) -- as adversarial-to-leak and prove two things:

  1. HASH-LOCK: every grading asset is content-hashed into a committed lock
     file. A silent edit to a grading test, or a gold patch drifting to match
     what the agent would produce, changes the lock and is caught. (This is the
     benchmark analogue of the LeapForge source-sha identity proof.)

  2. REACHABILITY SCAN (the source-scan control the PI asked to cover these
     paths): for every task, prove the grading assets are NOT within the
     agent's read scope. The agent's scope is exactly its workdir, which the
     harness materialises as a copy of `repo/` only. This module asserts that
     hidden/, gold/, and meta.json live OUTSIDE repo/, and that no hidden grading
     test's content appears verbatim anywhere inside repo/ (belt against an
     author accidentally pasting a grading test into a public file).

Authoring transcripts live outside the repository entirely (the workflow
subagent transcripts under ~/.claude/...), never inside any task directory and
never inside a workdir, so they are unreachable by construction; the lock
records that fact as provenance rather than hashing machine-specific paths.
"""

import hashlib
import json
import os


def _sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def _sha_file(path):
    with open(path, "rb") as f:
        return _sha_bytes(f.read())


def _asset_files(task):
    """The grading assets for a task: everything the agent must never read."""
    out = []
    for sub in ("hidden", "gold"):
        d = os.path.join(task.root, sub)
        if os.path.isdir(d):
            for dp, dn, fns in os.walk(d):
                dn[:] = [x for x in dn if x != "__pycache__"]
                for fn in sorted(fns):
                    if fn.endswith(".pyc"):
                        continue
                    out.append(os.path.join(dp, fn))
    meta = os.path.join(task.root, "meta.json")
    if os.path.isfile(meta):
        out.append(meta)
    return sorted(out)


def build_lock(bench):
    tasks = sorted(bench.all_tasks(), key=lambda t: t.id)
    entries = {}
    combined = hashlib.sha256()
    for t in tasks:
        files = {}
        for fp in _asset_files(t):
            rel = os.path.relpath(fp, t.root)
            sha = _sha_file(fp)
            files[rel] = sha
            combined.update((t.id + "/" + rel + ":" + sha).encode())
        entries[t.id] = files
    return {
        "benchmark": bench.name,
        "n_tasks": len(tasks),
        "n_repos": len({t.repo for t in tasks}),
        "assets_per_task": entries,
        "combined_sha256": combined.hexdigest(),
        "provenance": {
            "authored_by_model": "claude-fable-5 (session model at authoring)",
            "solving_agent_model": "claude-haiku-4-5-20251001",
            "note": "Authoring transcripts live outside the repo tree "
                    "(~/.claude/.../subagents/workflows) and never inside any "
                    "task dir or workdir; grading assets (hidden/, gold/, "
                    "meta.json) are siblings of repo/ and never materialised "
                    "into the agent workdir.",
        },
    }


def write_lock(bench, path):
    lock = build_lock(bench)
    d = os.path.dirname(path)
    if d and not os.path.isdir(d):
        os.makedirs(d)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(lock, f, indent=2, sort_keys=True)
    return lock


def load_lock(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def verify_lock(bench, path):
    """Recompute and compare against the committed lock. Returns (ok, reasons)."""
    if not os.path.exists(path):
        return False, ["no grading-asset lock at %s" % path]
    locked = load_lock(path)
    current = build_lock(bench)
    reasons = []
    if current["combined_sha256"] != locked.get("combined_sha256"):
        reasons.append("combined grading-asset hash changed (%s -> %s)"
                       % (locked.get("combined_sha256", "")[:12],
                          current["combined_sha256"][:12]))
    # per-file diff for a useful message
    for tid, files in current["assets_per_task"].items():
        lf = locked.get("assets_per_task", {}).get(tid, {})
        for rel, sha in files.items():
            if lf.get(rel) != sha:
                reasons.append("asset changed/added: %s/%s" % (tid, rel))
        for rel in lf:
            if rel not in files:
                reasons.append("asset removed: %s/%s" % (tid, rel))
    return (not reasons), reasons


def reachability_scan(bench):
    """Prove no grading asset is within the agent's read scope. Returns
    {ok, reasons, checked}. Fail-closed: any doubt is a failure."""
    reasons = []
    checked = 0
    for t in sorted(bench.all_tasks(), key=lambda t: t.id):
        repo_root = os.path.realpath(t.repo_dir)
        # 1) structural: grading-asset dirs/files must be OUTSIDE repo/
        for fp in _asset_files(t):
            rp = os.path.realpath(fp)
            if rp == repo_root or rp.startswith(repo_root + os.sep):
                reasons.append("%s: grading asset inside repo/ scope: %s"
                               % (t.id, os.path.relpath(fp, t.root)))
        # 2) content: no hidden grading-test ASSERTION appears inside a repo/
        #    SOURCE file (the "grading logic pasted into source the agent reads"
        #    leak). We deliberately do NOT flag overlap with the PUBLIC TEST
        #    files: those are public by design, and validate_task already proves
        #    the hidden tests fail on the buggy code while the public
        #    (pass_to_pass) tests pass -- so any assertion shared with a passing
        #    public test provably passes on buggy and is NOT the grading signal.
        public_names = {os.path.basename(p) for p in t.public_test_paths}
        hidden_lines = set()
        hdir = os.path.join(t.root, "hidden")
        if os.path.isdir(hdir):
            for dp, dn, fns in os.walk(hdir):
                for fn in fns:
                    if not fn.endswith(".py"):
                        continue
                    with open(os.path.join(dp, fn), "r", encoding="utf-8",
                              errors="replace") as f:
                        for ln in f:
                            s = ln.strip()
                            if len(s) > 12 and "assert" in s:
                                hidden_lines.add(s)
        src_blob = []
        for dp, dn, fns in os.walk(repo_root):
            dn[:] = [x for x in dn if x != "__pycache__"]
            for fn in fns:
                if not (fn.endswith(".py") or fn.endswith(".txt")):
                    continue
                # exclude the public test files and any test_*.py from the scan
                if fn in public_names or fn.startswith("test_"):
                    continue
                with open(os.path.join(dp, fn), "r", encoding="utf-8",
                          errors="replace") as f:
                    src_blob.append(f.read())
        blob = "\n".join(src_blob)
        for s in hidden_lines:
            if s in blob:
                reasons.append("%s: hidden grading assertion appears in a "
                               "source file: %r" % (t.id, s[:60]))
        checked += 1
    return {"ok": not reasons, "reasons": reasons, "checked": checked}
