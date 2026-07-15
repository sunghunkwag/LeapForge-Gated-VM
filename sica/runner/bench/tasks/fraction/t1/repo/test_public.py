"""Public regression guard for fraction/t1.

Every assertion here already holds on the shipped code: they all use a
positive denominator, so the reported sign-normalization problem (which only
shows up when a fraction is built with a negative denominator) never affects
them. They protect the reduce / add / compare paths from being broken by a
fix.
"""

from core import Fraction, add, compare


def test_reduces_to_lowest_terms():
    f = Fraction(2, 4)
    assert (f.num, f.den) == (1, 2)
    g = Fraction(6, 3)
    assert (g.num, g.den) == (2, 1)


def test_negative_numerator_positive_denominator():
    f = Fraction(-2, 4)
    assert (f.num, f.den) == (-1, 2)


def test_equality_of_equal_values():
    assert Fraction(1, 2) == Fraction(2, 4)
    assert Fraction(3, 6) == Fraction(1, 2)


def test_add_positive_fractions():
    assert add(Fraction(1, 2), Fraction(1, 3)) == Fraction(5, 6)
    assert add(Fraction(1, 4), Fraction(1, 4)) == Fraction(1, 2)


def test_compare_positive_fractions():
    assert compare(Fraction(1, 3), Fraction(1, 2)) == -1
    assert compare(Fraction(1, 2), Fraction(1, 2)) == 0
    assert compare(Fraction(3, 4), Fraction(1, 2)) == 1
