"""Public regression guard for intervals.insert (passes on the shipped snapshot).

These cases cover insertion with no absorption and absorption where the
inserted interval does not extend past the intervals it swallows.  They keep
working on the current code and guard against a fix that breaks them.
"""

from core import insert


def test_insert_into_empty():
    assert insert([], [2, 4]) == [[2, 4]]


def test_insert_disjoint_before():
    assert insert([[10, 20]], [1, 3]) == [[1, 3], [10, 20]]


def test_insert_disjoint_after():
    assert insert([[1, 3]], [10, 20]) == [[1, 3], [10, 20]]


def test_insert_between_without_overlap():
    assert insert([[1, 3], [7, 9]], [4, 5]) == [[1, 3], [4, 5], [7, 9]]


def test_new_fully_inside_existing():
    assert insert([[1, 5]], [2, 3]) == [[1, 5]]


def test_absorb_interval_that_extends_further():
    # the swallowed interval ends beyond ``new``; the combined end is correct.
    assert insert([[4, 10]], [2, 6]) == [[2, 10]]


def test_absorb_touching_interval_that_extends_further():
    # ``new`` touches an existing interval that reaches further right; the
    # combined end comes from the absorbed interval, so this already works.
    assert insert([[3, 9]], [1, 3]) == [[1, 9]]
