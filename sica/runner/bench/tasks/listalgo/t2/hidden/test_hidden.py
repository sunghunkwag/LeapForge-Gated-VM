"""Hidden grading tests for listalgo/t2 (dedup calls must be independent)."""

from core import dedup


def test_repeated_calls_are_independent():
    first = dedup([1, 2, 3])
    second = dedup([1, 2, 3])
    assert first == [1, 2, 3]
    assert second == [1, 2, 3]


def test_second_call_same_elements():
    dedup([7, 8, 9])
    assert dedup([7, 8, 9]) == [7, 8, 9]


def test_no_state_leak_between_calls():
    dedup(["x", "y"])
    assert dedup(["x", "y", "z", "y"]) == ["x", "y", "z"]


def test_preserves_order_and_dedups():
    assert dedup([3, 1, 3, 2, 1]) == [3, 1, 2]


def test_fresh_result_every_time():
    for _ in range(3):
        assert dedup([5, 6, 5]) == [5, 6]


def test_default_argument_not_mutated():
    dedup([100, 200])
    # A later call on unrelated values must be unaffected by earlier ones.
    assert dedup([200, 100]) == [200, 100]
