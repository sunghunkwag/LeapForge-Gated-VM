"""Hidden grading tests for intervals.insert (the fail->pass signal).

The reported bug is that when the inserted interval extends past an absorbed
interval (in particular when it fully contains a shorter one), the combined
interval's end is truncated to the absorbed interval's end instead of keeping
the larger of the two.
"""

from core import insert


def test_new_contains_existing():
    assert insert([[4, 6]], [2, 10]) == [[2, 10]]


def test_new_extends_past_single_absorbed():
    assert insert([[10, 12]], [5, 30]) == [[5, 30]]


def test_new_extends_past_last_of_several():
    assert insert([[3, 5], [7, 8]], [1, 20]) == [[1, 20]]


def test_touching_left_extends_right():
    # [1, 3] touches [3, 5] at 3; the merged interval must reach 5, not 3.
    assert insert([[1, 3]], [3, 5]) == [[1, 5]]


def test_new_contains_multiple_and_extends():
    assert insert([[2, 4], [6, 8]], [1, 20]) == [[1, 20]]


def test_absorb_then_keep_tail():
    assert insert([[3, 4], [10, 12]], [1, 6]) == [[1, 6], [10, 12]]


def test_non_manifesting_cases_still_correct():
    # regression: cases that already worked must keep working.
    assert insert([], [2, 4]) == [[2, 4]]
    assert insert([[10, 20]], [1, 3]) == [[1, 3], [10, 20]]
    assert insert([[4, 10]], [2, 6]) == [[2, 10]]
    assert insert([[1, 5]], [2, 3]) == [[1, 5]]
