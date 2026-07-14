from main import scaled_sum


def test_scaled_sum_contract():
    assert scaled_sum([], 5) == 0
    assert scaled_sum([], 0) == 0
    assert isinstance(scaled_sum([1, 2, 3], 4), int)
