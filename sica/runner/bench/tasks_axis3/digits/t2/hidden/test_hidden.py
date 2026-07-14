from main import nth_digit


def test_ones_place():
    assert nth_digit(123, 1) == 3
    assert nth_digit(5, 1) == 5
    assert nth_digit(40, 1) == 0
    assert nth_digit(709, 1) == 9


def test_higher_places():
    assert nth_digit(123, 2) == 2
    assert nth_digit(123, 3) == 1
    assert nth_digit(8064, 3) == 0
    assert nth_digit(8064, 4) == 8


def test_across_a_number():
    n = 92037
    assert nth_digit(n, 1) == 7
    assert nth_digit(n, 2) == 3
    assert nth_digit(n, 3) == 0
    assert nth_digit(n, 4) == 2
    assert nth_digit(n, 5) == 9
