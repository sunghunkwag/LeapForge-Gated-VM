"""Public regression guard for listalgo/t2.

Every assertion here holds on the buggy snapshot: each dedup call below uses
its own disjoint set of values, so the reported cross-call state leak never
changes these results. The failure only shows up when a call repeats values
that an earlier call already consumed -- see the reported issue.
"""

from core import chunk, dedup, running_max


def test_dedup_basic_removes_duplicates():
    assert dedup([1, 1, 2, 3, 2, 3]) == [1, 2, 3]


def test_dedup_disjoint_numbers():
    assert dedup([10, 20, 20, 30, 10]) == [10, 20, 30]


def test_dedup_strings():
    assert dedup(["a", "b", "a", "c", "b"]) == ["a", "b", "c"]


def test_chunk_and_running_max_unaffected():
    assert chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
    assert running_max([1, 3, 2, 5, 4]) == [1, 3, 3, 5, 5]
