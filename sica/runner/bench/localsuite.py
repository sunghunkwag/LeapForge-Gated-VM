"""localsuite -- the bundled, offline, repo-disjoint bug-fix benchmark that
drives the engine loop.

Why this and not SWE-bench Verified for the loop: SWE-bench Verified is the
maintained real-repo standard and is pinned here as the `full`/transfer
backend (see swebench.py), but each of its instances needs a multi-GB Docker
image and network to registries that this sandbox does not permit, and an
unattended smoke cannot build hundreds of them inside the token/time budget.
localsuite keeps every property that makes the score MEAN capability -- a real
repo, a genuine bug, hidden fail->pass grading tests the agent cannot read, a
repository-disjoint split -- while running fully offline and deterministically
so the engine can iterate. Tasks are pure-stdlib Python so grading needs no
network and no pip install.

The suite is content-pinned: `pin()` hashes every task asset, so a silent edit
to a task (or a leaked grading test) changes the pin and is caught.
"""

import hashlib
import os

from .base import Benchmark, Task, load_meta

_HERE = os.path.dirname(os.path.abspath(__file__))
TASKS_ROOT = os.path.join(_HERE, "tasks")


class LocalSuite(Benchmark):
    name = "localsuite"

    def __init__(self, tasks_root=None):
        self.tasks_root = tasks_root or TASKS_ROOT
        self._tasks = None

    def all_tasks(self):
        if self._tasks is not None:
            return self._tasks
        tasks = []
        if os.path.isdir(self.tasks_root):
            for repo in sorted(os.listdir(self.tasks_root)):
                rdir = os.path.join(self.tasks_root, repo)
                if not os.path.isdir(rdir):
                    continue
                for tk in sorted(os.listdir(rdir)):
                    tdir = os.path.join(rdir, tk)
                    meta_p = os.path.join(tdir, "meta.json")
                    if os.path.isfile(meta_p):
                        tasks.append(Task(tdir, load_meta(tdir)))
        self._tasks = tasks
        return tasks

    def pin(self):
        """Content hash over every task asset (excludes __pycache__)."""
        h = hashlib.sha256()
        for t in sorted(self.all_tasks(), key=lambda t: t.id):
            for dp, dn, fns in os.walk(t.root):
                dn[:] = sorted(d for d in dn if d != "__pycache__")
                for fn in sorted(fns):
                    if fn.endswith(".pyc"):
                        continue
                    fp = os.path.join(dp, fn)
                    rp = os.path.relpath(fp, self.tasks_root)
                    h.update(rp.encode())
                    with open(fp, "rb") as f:
                        h.update(f.read())
        return {"benchmark": self.name, "n_tasks": len(self.all_tasks()),
                "n_repos": len({t.repo for t in self.all_tasks()}),
                "content_sha256": h.hexdigest()}
