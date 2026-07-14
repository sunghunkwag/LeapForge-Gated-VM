from main import from_digits


def test_empty_is_zero():
    assert from_digits([], 10) == 0
    assert from_digits([], 2) == 0


def test_all_zero_digits_is_zero():
    assert from_digits([0], 10) == 0
    assert from_digits([0, 0, 0], 10) == 0
    assert from_digits([0, 0], 2) == 0


def test_returns_int():
    assert isinstance(from_digits([1, 2, 3], 10), int)
    assert isinstance(from_digits([1, 0, 1], 2), int)


def test_is_deterministic():
    assert from_digits([4, 5, 6], 10) == from_digits([4, 5, 6], 10)
