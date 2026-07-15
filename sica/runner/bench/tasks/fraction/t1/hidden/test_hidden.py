"""Hidden grading tests for fraction/t1.

A fraction built with a negative denominator must be normalized so the sign
lives on the numerator and the denominator is always positive. These cases
FAIL on the buggy snapshot (which leaves the negative sign on the denominator)
and PASS once the constructor normalizes the sign.
"""

from core import Fraction, add, compare


def test_negative_denominator_moves_sign_to_numerator():
    f = Fraction(1, -2)
    assert (f.num, f.den) == (-1, 2)


def test_both_negative_becomes_positive():
    f = Fraction(-3, -6)
    assert (f.num, f.den) == (1, 2)
    assert f == Fraction(1, 2)


def test_denominator_is_always_positive():
    for n, d in [(3, -4), (-5, -10), (7, -1), (0, -3)]:
        assert Fraction(n, d).den > 0


def test_equal_values_with_opposite_representations():
    assert Fraction(1, -2) == Fraction(-1, 2)
    assert Fraction(-4, -8) == Fraction(1, 2)


def test_add_with_negative_denominator_input():
    # -1/2 + 1/2 == 0, canonicalized as 0/1.
    result = add(Fraction(1, -2), Fraction(1, 2))
    assert (result.num, result.den) == (0, 1)
    # 1/-3 + 1/6 == -1/6.
    result = add(Fraction(1, -3), Fraction(1, 6))
    assert result == Fraction(-1, 6)


def test_compare_handles_negative_denominators():
    assert compare(Fraction(1, -2), Fraction(-1, 2)) == 0
    assert compare(Fraction(1, -2), Fraction(1, 4)) == -1
