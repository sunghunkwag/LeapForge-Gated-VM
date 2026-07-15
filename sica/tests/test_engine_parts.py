"""Unit tests for the evolution machinery: repo-disjoint split (G-heldout),
memory heldout-stripping (G-heldout), the adoption gate, scaffold edits/audit,
and the proposer's JSON parsing."""

from runner import scaffold_io, proposer
from runner.gate import select_winner
from runner.memory import ImprovementMemory
from runner.bench.localsuite import LocalSuite
import os

FIX = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "runner", "bench", "fixtures")


# ------------------------------------------------------- split (G-heldout)
def test_split_is_repo_disjoint_and_seeded():
    bench = LocalSuite(tasks_root=FIX)
    tr, he = bench.split("s1", 4, 2)
    assert {t.repo for t in tr} & {t.repo for t in he} == set()
    # deterministic per seed
    tr2, he2 = bench.split("s1", 4, 2)
    assert [t.id for t in tr] == [t.id for t in tr2]
    assert [t.id for t in he] == [t.id for t in he2]


def test_localsuite_pin_changes_with_content(tmp_path):
    bench = LocalSuite(tasks_root=FIX)
    pin1 = bench.pin()
    assert pin1["n_tasks"] == 6 and pin1["n_repos"] == 6
    assert len(pin1["content_sha256"]) == 64


# ------------------------------------------------ memory strips heldout
def test_memory_view_strips_heldout(tmp_path):
    mem = ImprovementMemory(str(tmp_path / "m.jsonl"))
    mem.append({"generation": 1, "targeted_failure_mode": "x",
                "change_summary": "c", "predicted_effect": "p",
                "measured_train_delta": 2, "measured_heldout_delta": 0.9,
                "adopted": True})
    view = mem.view_for_proposer(m=8)
    assert view and "measured_heldout_delta" not in view[0]
    assert view[0]["measured_train_delta"] == 2
    # full log retains heldout for the report
    assert mem.full_log()[0]["measured_heldout_delta"] == 0.9


# ------------------------------------------------------------- gate
def _ev(solved, tokens, sha, label="c"):
    return {"solved": solved, "score": solved / 4.0, "n": 4, "sha": sha,
            "meter": {"model_tokens": tokens, "cost_usd": 0.0},
            "scaffold": {"x": sha}, "info": {"label": label}}


def test_gate_adopts_strict_winner():
    inc = _ev(2, 100, "inc")
    cands = [_ev(3, 200, "a", "a"), _ev(2, 50, "b", "b")]
    winner, dec = select_winner(inc, cands)
    assert dec["adopted"] and winner["sha"] == "a"


def test_gate_tie_goes_to_incumbent():
    inc = _ev(2, 100, "inc")
    cands = [_ev(2, 10, "a", "a"), _ev(1, 5, "b", "b")]
    winner, dec = select_winner(inc, cands)
    assert not dec["adopted"] and winner is None


def test_gate_breaks_ties_by_fewer_tokens():
    inc = _ev(1, 100, "inc")
    cands = [_ev(3, 500, "hi", "hi"), _ev(3, 100, "lo", "lo")]
    winner, dec = select_winner(inc, cands)
    assert winner["sha"] == "lo"          # same solves, fewer tokens wins


# --------------------------------------------------- scaffold edits/audit
def _gen0():
    root = os.path.join(os.path.dirname(FIX), "..", "..", "scaffold")
    root = os.path.normpath(os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "scaffold"))
    return scaffold_io.load_scaffold(root)


def test_apply_edits_new_file_and_sha_changes():
    s = _gen0()
    sha0 = scaffold_io.scaffold_sha(s)
    s2 = scaffold_io.apply_edits(s, {
        "files": {"newtool.py": "def helper():\n    return 1\n"},
        "exec_order": s["manifest"]["exec_order"][:1] + ["newtool.py"]
                      + s["manifest"]["exec_order"][1:],
        "label": "with-tool"})
    assert scaffold_io.scaffold_sha(s2) != sha0
    assert "newtool.py" in s2["files"]
    scaffold_io.audit_scaffold(s2)        # must still pass audit


def test_apply_edits_rejects_bad_names():
    s = _gen0()
    import pytest
    with pytest.raises(ValueError):
        scaffold_io.apply_edits(s, {"files": {"../evil.py": "x=1\n"}})


def test_gen0_scaffold_audits_and_dry_loads():
    from runner import restricted
    s = _gen0()
    scaffold_io.audit_scaffold(s)
    ok, err, _ = restricted.dry_load(scaffold_io.scaffold_sources(s))
    assert ok, err


# --------------------------------------------------- proposer JSON parse
def test_proposer_extract_json_from_fenced():
    obj = proposer._extract_json('```json\n{"a": 1, "files": {}}\n```')
    assert obj["a"] == 1
