from main import scaled_sum


def test_scaled_sum_values():
    assert scaled_sum([1, 2, 3], 10) == 60
    assert scaled_sum([2, 4], 5) == 30
    assert scaled_sum([5], 3) == 15
    assert scaled_sum([0, 0, 0], 7) == 0
    assert scaled_sum([], 9) == 0
    assert scaled_sum([10], 10) == 100
