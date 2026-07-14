from main import count_in_range


def test_upper_bound_is_inclusive():
    assert count_in_range([1, 2, 3, 4, 5], 2, 4) == 3       # 2, 3, 4
    assert count_in_range([10], 0, 10) == 1                 # equal to hi
    assert count_in_range([5, 5, 5], 1, 5) == 3            # all equal to hi


def test_both_bounds_inclusive():
    assert count_in_range([1, 2, 3], 1, 3) == 3            # both endpoints
    assert count_in_range([0, 1, 2], 0, 0) == 1           # single-point range


def test_values_outside_range_excluded():
    assert count_in_range([1, 2, 3], 4, 6) == 0
    assert count_in_range([-5, 0, 5], -1, 1) == 1         # only 0
    assert count_in_range([], 0, 10) == 0
