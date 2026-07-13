"""Task / Benchmark interfaces and the repository-disjoint split (G-heldout).

A Task is a self-contained bug-fix problem:
  repo/    -- a pristine buggy snapshot (source + PUBLIC tests the agent may run)
  gold/    -- fixed versions of exactly the editable files (the reference patch)
  hidden/  -- grading tests, never placed in the agent's workdir (G-isolate)
  meta.json:
    repo, task, issue, difficulty,
    editable_files      : the fix surface; grading reads back only these
    public_test_paths   : tests visible to the agent (relative to repo/)
    fail_to_pass         : hidden pytest targets that must go FAIL -> PASS
    pass_to_pass         : pytest targets that must stay PASS (regression guard)

The train/heldout split is REPOSITORY-disjoint: no repo contributes tasks to
both slices. Trained-and-scored-on-the-same-repo would let scaffold changes
memorise repo-specific quirks and call it capability -- the split forbids it.
"""

import json
import os

from ..prng import XorShift64Star


class Task(object):
    def __init__(self, root, meta):
        self.root = root                       # .../tasks/<repo>/<task>
        self.repo = meta["repo"]
        self.task = meta["task"]
        self.id = "%s/%s" % (self.repo, self.task)
        self.issue = meta.get("issue", "")
        self.difficulty = meta.get("difficulty", "unknown")
        self.editable_files = list(meta["editable_files"])
        self.public_test_paths = list(meta["public_test_paths"])
        self.fail_to_pass = list(meta["fail_to_pass"])
        self.pass_to_pass = list(meta.get("pass_to_pass", []))
        self.meta = meta

    @property
    def repo_dir(self):
        return os.path.join(self.root, "repo")

    @property
    def gold_dir(self):
        return os.path.join(self.root, "gold")

    @property
    def hidden_dir(self):
        return os.path.join(self.root, "hidden")

    def repo_files(self):
        out = []
        for dp, dn, fns in os.walk(self.repo_dir):
            dn[:] = [d for d in dn if d != "__pycache__"]
            for fn in fns:
                rp = os.path.relpath(os.path.join(dp, fn), self.repo_dir)
                out.append(rp)
        return sorted(out)

    def public_dict(self):
        """What the broker hands the scaffold (no hidden info)."""
        return {
            "name": self.id,
            "issue": self.issue,
            "editable_files": self.editable_files,
            "files": self.repo_files(),
            "test_command": (["python", "-m", "pytest"]
                             + self.public_test_paths),
        }


class Benchmark(object):
    name = "base"
    pin = None

    def all_tasks(self):
        raise NotImplementedError

    def split(self, seed, n_train, n_heldout):
        """Repository-disjoint, seeded, fixed per seed."""
        tasks = self.all_tasks()
        by_repo = {}
        for t in tasks:
            by_repo.setdefault(t.repo, []).append(t)
        for r in by_repo:
            by_repo[r].sort(key=lambda t: t.id)
        repos = sorted(by_repo)
        prng = XorShift64Star("split|%s|%s" % (self.name, seed))
        prng.shuffle(repos)

        train, heldout = [], []
        # Greedily assign whole repos to the slice that still needs tasks,
        # keeping the split repository-disjoint by construction.
        for r in repos:
            rtasks = by_repo[r]
            if len(train) < n_train and (
                    len(train) - n_train <= len(heldout) - n_heldout
                    or len(heldout) >= n_heldout):
                train.extend(rtasks)
            elif len(heldout) < n_heldout:
                heldout.extend(rtasks)
            elif len(train) < n_train:
                train.extend(rtasks)
        train = sorted(train, key=lambda t: t.id)[:n_train]
        heldout = sorted(heldout, key=lambda t: t.id)[:n_heldout]

        train_repos = {t.repo for t in train}
        heldout_repos = {t.repo for t in heldout}
        overlap = train_repos & heldout_repos
        if overlap:
            raise ValueError("split not repo-disjoint: %s" % sorted(overlap))
        return train, heldout


def load_meta(task_root):
    with open(os.path.join(task_root, "meta.json"), "r",
              encoding="utf-8") as f:
        return json.load(f)
