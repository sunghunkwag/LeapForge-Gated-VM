"""Append-only, hash-chained ledger (same contract as the LeapForge lineage).

Every generation snapshots its gate results, adopted change, meter totals, and
held-out score here. The chain makes the run tamper-evident: a preserved
ledger on auto-halt is the audit trail the directive requires (section 4/5).
"""

import hashlib
import json
import os

GENESIS_PREV = "0" * 64


def canon(body):
    return json.dumps(body, sort_keys=True, separators=(",", ":"))


def record_hash(prev_hash, body):
    return hashlib.sha256((prev_hash + canon(body)).encode()).hexdigest()


class Ledger(object):
    def __init__(self, path):
        self.path = path                     # path=None -> in-memory only
        self.records = []
        self.prev = GENESIS_PREV
        if path is not None and os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        self.records.append(json.loads(line))
            self.verify()
            if self.records:
                self.prev = self.records[-1]["hash"]

    def verify(self):
        prev = GENESIS_PREV
        for i, rec in enumerate(self.records):
            if rec["prev"] != prev:
                raise ValueError("LEDGER BROKEN at record %d (prev)" % i)
            if record_hash(prev, rec["body"]) != rec["hash"]:
                raise ValueError("LEDGER BROKEN at record %d (hash)" % i)
            prev = rec["hash"]
        return True

    def append(self, kind, body):
        rec = {"kind": kind, "body": body, "prev": self.prev,
               "hash": record_hash(self.prev, body)}
        self.records.append(rec)
        if self.path is not None:
            d = os.path.dirname(self.path)
            if d and not os.path.isdir(d):
                os.makedirs(d)
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(canon(rec) + "\n")
        self.prev = rec["hash"]
        return rec["hash"]

    def find(self, kind, **match):
        out = []
        for rec in self.records:
            if rec["kind"] != kind:
                continue
            if all(rec["body"].get(k) == v for k, v in match.items()):
                out.append(rec)
        return out
