from main import nth_digit


def test_returns_int():
    assert isinstance(nth_digit(123, 1), int)
    assert isinstance(nth_digit(0, 1), int)
    assert isinstance(nth_digit(9, 2), int)


def test_out_of_range_place_is_zero():
    # Asking for a place beyond the number's digits gives 0.
    assert nth_digit(4, 5) == 0
    assert nth_digit(70, 6) == 0
    assert nth_digit(0, 3) == 0


def test_is_deterministic():
    assert nth_digit(246, 2) == nth_digit(246, 2)
    assert nth_digit(1000, 4) == nth_digit(1000, 4)
