"""Scaffold archive + quality-diversity escape (directive section 1.4).

Every accepted scaffold is kept with its train + heldout scores and the failure
mode its change targeted. If held-out fails to improve for `stall` generations,
the engine branches from the best PRIOR archived scaffold along a DIFFERENT
failure mode, rather than grinding the current local optimum.
"""

import json
import os

from . import scaffold_io


class Archive(object):
    def __init__(self, root):
        self.root = root
        self.index_path = os.path.join(root, "index.jsonl")
        self.entries = []
        if os.path.exists(self.index_path):
            with open(self.index_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        self.entries.append(json.loads(line))

    def add(self, scaffold, generation, train_score, heldout_score,
            targeted_failure_mode, change_summary, adopted):
        sha = scaffold_io.scaffold_sha(scaffold)
        subdir = os.path.join(self.root, "gen%02d_%s" % (generation, sha))
        scaffold_io.save_scaffold(scaffold, subdir)
        entry = {
            "generation": generation,
            "sha": sha,
            "dir": os.path.relpath(subdir, self.root),
            "train_score": train_score,
            "heldout_score": heldout_score,
            "targeted_failure_mode": targeted_failure_mode,
            "change_summary": change_summary,
            "adopted": adopted,
        }
        self.entries.append(entry)
        if not os.path.isdir(self.root):
            os.makedirs(self.root)
        with open(self.index_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, separators=(",", ":")) + "\n")
        return entry

    def best_prior(self, exclude_sha=None, by="train_score"):
        """Best archived scaffold by a score key (train by default -- heldout
        must not drive selection). Ties broken toward the earlier generation."""
        cands = [e for e in self.entries if e["sha"] != exclude_sha]
        if not cands:
            return None
        cands.sort(key=lambda e: (-(e.get(by) or 0.0), e["generation"]))
        return cands[0]

    def modes_tried_since(self, sha):
        """Failure modes targeted by descendants recorded after `sha` appeared
        -- used to pick a DIFFERENT mode on a QD restart."""
        modes = []
        seen = False
        for e in self.entries:
            if seen and e.get("targeted_failure_mode"):
                modes.append(e["targeted_failure_mode"])
            if e["sha"] == sha:
                seen = True
        return modes

    def load(self, entry):
        return scaffold_io.load_scaffold(os.path.join(self.root, entry["dir"]))
