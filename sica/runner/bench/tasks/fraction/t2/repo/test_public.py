"""Public regression guard for fraction/t2.

Every assertion here already holds on the shipped code. The add() cases all
combine fractions that already share a denominator, which the current code
handles correctly; they guard the same-denominator path, plus reduction, sign
normalization and comparison, against being broken by a fix.
"""

from core import Fraction, add, compare


def test_add_same_denominator():
    assert add(Fraction(1, 4), Fraction(1, 4)) == Fraction(1, 2)
    assert add(Fraction(2, 5), Fraction(1, 5)) == Fraction(3, 5)
    assert add(Fraction(1, 3), Fraction(1, 3)) == Fraction(2, 3)


def test_add_result_is_reduced():
    assert add(Fraction(1, 6), Fraction(1, 6)) == Fraction(1, 3)


def test_reduces_to_lowest_terms():
    assert (Fraction(4, 8).num, Fraction(4, 8).den) == (1, 2)


def test_sign_normalization():
    assert Fraction(1, -2) == Fraction(-1, 2)
    assert Fraction(-4, -8) == Fraction(1, 2)


def test_equality_and_compare():
    assert Fraction(1, 2) == Fraction(2, 4)
    assert compare(Fraction(1, 4), Fraction(3, 4)) == -1
    assert compare(Fraction(3, 4), Fraction(1, 4)) == 1
    assert compare(Fraction(1, 2), Fraction(2, 4)) == 0
