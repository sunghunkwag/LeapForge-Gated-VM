"""Public regression guard for intervals (passes on the shipped snapshot).

These cases exercise the clearly-overlapping and clearly-disjoint paths that
already work.  They protect against a fix that breaks those paths while
addressing the reported problem.
"""

from core import merge, overlaps


def test_empty():
    assert merge([]) == []


def test_single_interval():
    assert merge([[1, 3]]) == [[1, 3]]


def test_disjoint_with_gap_kept_separate():
    assert merge([[1, 5], [7, 9]]) == [[1, 5], [7, 9]]


def test_clearly_overlapping_merged():
    assert merge([[1, 5], [2, 8]]) == [[1, 8]]


def test_contained_interval_absorbed():
    assert merge([[1, 10], [2, 5]]) == [[1, 10]]


def test_unsorted_disjoint_input_is_ordered():
    assert merge([[4, 6], [1, 3]]) == [[1, 3], [4, 6]]


def test_overlaps_helper():
    assert overlaps([1, 3], [3, 5]) is True
    assert overlaps([1, 3], [4, 5]) is False
    assert overlaps([1, 10], [2, 3]) is True
