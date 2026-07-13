"""Cross-generation improvement memory (directive section 1.3).

An append-only log of {change, targeted failure mode, predicted effect,
measured train delta, measured heldout delta, adopted?}. The last M entries are
fed into each proposal step so the agent learns which KINDS of changes paid off
and stops re-proposing dead ones -- the compounding mechanism.

CRITICAL (G-heldout): the proposer view STRIPS the measured heldout deltas.
Proposals and the gate must never see held-out results, or the engine optimises
the thermometer instead of the temperature. Heldout is retained in the full log
for the report only.
"""

import json
import os


class ImprovementMemory(object):
    def __init__(self, path):
        self.path = path
        self.entries = []
        if path and os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        self.entries.append(json.loads(line))

    def append(self, entry):
        self.entries.append(entry)
        if self.path:
            d = os.path.dirname(self.path)
            if d and not os.path.isdir(d):
                os.makedirs(d)
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, separators=(",", ":")) + "\n")

    def view_for_proposer(self, m=8):
        """Heldout-free recent history for the proposer (G-heldout)."""
        view = []
        for e in self.entries[-m:]:
            view.append({
                "generation": e.get("generation"),
                "targeted_failure_mode": e.get("targeted_failure_mode"),
                "change_summary": e.get("change_summary"),
                "predicted_effect": e.get("predicted_effect"),
                "measured_train_delta": e.get("measured_train_delta"),
                "adopted": e.get("adopted"),
                # NB: measured_heldout_delta deliberately omitted.
            })
        return view

    def full_log(self):
        return list(self.entries)
