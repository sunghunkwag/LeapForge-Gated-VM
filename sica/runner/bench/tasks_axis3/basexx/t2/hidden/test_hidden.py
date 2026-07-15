from main import from_digits


def test_decimal_values():
    assert from_digits([1, 2, 3], 10) == 123
    assert from_digits([9], 10) == 9
    assert from_digits([1, 0], 10) == 10
    assert from_digits([7, 0, 5], 10) == 705


def test_binary_values():
    assert from_digits([1, 0, 1], 2) == 5
    assert from_digits([1, 1, 1, 1], 2) == 15
    assert from_digits([1, 0, 0, 0], 2) == 8


def test_other_bases():
    assert from_digits([1, 0], 7) == 7
    assert from_digits([6, 6], 7) == 48
    assert from_digits([1, 2, 3], 16) == 291
