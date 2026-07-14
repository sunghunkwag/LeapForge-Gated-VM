from main import remaining_capacity


def test_remaining_capacity_returns_int():
    assert isinstance(remaining_capacity(100, []), int)
    assert isinstance(remaining_capacity(50, [10]), int)


def test_empty_scale_has_full_limit():
    assert remaining_capacity(100, []) == 100
    assert remaining_capacity(0, []) == 0


def test_remaining_capacity_is_deterministic():
    assert remaining_capacity(80, [10, 20]) == remaining_capacity(80, [10, 20])
