"""Hidden grading tests for intervals.merge (the fail->pass signal).

The reported bug is that closed intervals which only touch at a shared endpoint
are not merged.  These cases assert the correct closed-interval behaviour.
"""

from core import merge


def test_touching_intervals_merge():
    assert merge([[1, 3], [3, 5]]) == [[1, 5]]


def test_chain_of_touching_intervals():
    assert merge([[1, 2], [2, 3], [3, 4]]) == [[1, 4]]


def test_touching_unsorted_input():
    assert merge([[5, 7], [1, 3], [3, 5]]) == [[1, 7]]


def test_single_point_touch():
    assert merge([[1, 3], [3, 3]]) == [[1, 3]]
    assert merge([[2, 2], [2, 5]]) == [[2, 5]]


def test_touch_then_gap():
    # first two touch and merge; the third is a genuinely separate interval.
    assert merge([[1, 3], [3, 6], [8, 9]]) == [[1, 6], [8, 9]]


def test_overlap_and_touch_mixed():
    assert merge([[1, 4], [2, 6], [6, 10]]) == [[1, 10]]


def test_disjoint_paths_still_correct():
    # regression: the clearly-disjoint and clearly-overlapping paths must
    # keep working after the boundary is fixed.
    assert merge([]) == []
    assert merge([[1, 5], [7, 9]]) == [[1, 5], [7, 9]]
    assert merge([[1, 10], [2, 5]]) == [[1, 10]]
