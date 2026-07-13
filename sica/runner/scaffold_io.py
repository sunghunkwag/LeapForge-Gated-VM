"""Load / audit / hash / persist a scaffold.

A scaffold is {manifest, files}: manifest.exec_order lists the .py files (in
the order they are exec'd into one shared namespace), and files maps each name
to its source. The broker wants sources as [[name, src], ...] in exec order.
Every scaffold is audited (audit.py) before it is ever executed.
"""

import copy
import hashlib
import json
import os

from . import audit


def load_scaffold(scaffold_dir):
    with open(os.path.join(scaffold_dir, "manifest.json"), "r",
              encoding="utf-8") as f:
        manifest = json.load(f)
    files = {}
    for name in manifest["exec_order"]:
        with open(os.path.join(scaffold_dir, name), "r",
                  encoding="utf-8") as f:
            files[name] = f.read()
    return {"manifest": manifest, "files": files}


def scaffold_sources(scaffold):
    return [[name, scaffold["files"][name]]
            for name in scaffold["manifest"]["exec_order"]]


def audit_scaffold(scaffold):
    """Raise audit.AuditError on any violation; return per-file reports."""
    return audit.audit_scaffold_files(scaffold["files"])


def scaffold_sha(scaffold):
    h = hashlib.sha256()
    h.update(json.dumps(scaffold["manifest"], sort_keys=True,
                        separators=(",", ":")).encode())
    for name in scaffold["manifest"]["exec_order"]:
        h.update(("\x00" + name + "\x00").encode())
        h.update(scaffold["files"][name].encode("utf-8"))
    return h.hexdigest()[:16]


def clone(scaffold):
    return copy.deepcopy(scaffold)


def save_scaffold(scaffold, dest_dir):
    if not os.path.isdir(dest_dir):
        os.makedirs(dest_dir)
    with open(os.path.join(dest_dir, "manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump(scaffold["manifest"], f, indent=2)
    for name, src in scaffold["files"].items():
        p = os.path.join(dest_dir, name)
        d = os.path.dirname(p)
        if d and not os.path.isdir(d):
            os.makedirs(d)
        with open(p, "w", encoding="utf-8") as f:
            f.write(src)


def apply_edits(scaffold, edits):
    """edits: {"files": {name: new_src, ...}, "exec_order": [...optional...]}.
    Returns a NEW scaffold (does not mutate the input). New files may be added;
    exec_order may be replaced (must reference existing/added files)."""
    new = clone(scaffold)
    for name, src in (edits.get("files") or {}).items():
        if not isinstance(name, str) or not name.endswith(".py"):
            raise ValueError("bad scaffold file name: %r" % name)
        if "/" in name or "\\" in name or name.startswith("."):
            raise ValueError("scaffold file must be a bare .py name: %r" % name)
        new["files"][name] = src if isinstance(src, str) else str(src)
    if edits.get("exec_order"):
        order = list(edits["exec_order"])
        for name in order:
            if name not in new["files"]:
                raise ValueError("exec_order references missing file: %r"
                                 % name)
        new["manifest"] = dict(new["manifest"])
        new["manifest"]["exec_order"] = order
    # entry must still be present as a defined solve(); enforced at run time.
    new["manifest"] = dict(new["manifest"])
    new["manifest"]["scaffold_version"] = edits.get(
        "label", new["manifest"].get("scaffold_version", "child"))
    return new
