"""Hidden grading tests for fraction/t2.

Adding two fractions with UNLIKE denominators must scale each numerator by its
own factor before summing. These cases FAIL on the buggy snapshot (which scales
both numerators by the first fraction's factor) and PASS once add() scales each
numerator correctly.
"""

from core import Fraction, add


def test_add_unlike_denominators():
    assert add(Fraction(1, 2), Fraction(1, 3)) == Fraction(5, 6)
    assert add(Fraction(1, 2), Fraction(1, 4)) == Fraction(3, 4)
    assert add(Fraction(1, 6), Fraction(1, 3)) == Fraction(1, 2)


def test_add_larger_unlike_denominators():
    assert add(Fraction(2, 3), Fraction(3, 4)) == Fraction(17, 12)
    assert add(Fraction(3, 10), Fraction(2, 15)) == Fraction(13, 30)


def test_add_with_negatives():
    assert add(Fraction(-1, 2), Fraction(1, 3)) == Fraction(-1, 6)
    assert add(Fraction(1, 2), Fraction(-1, 3)) == Fraction(1, 6)


def test_add_is_commutative():
    assert add(Fraction(1, 3), Fraction(1, 2)) == add(Fraction(1, 2),
                                                       Fraction(1, 3))
    assert add(Fraction(2, 7), Fraction(3, 5)) == add(Fraction(3, 5),
                                                      Fraction(2, 7))


def test_add_coprime_denominators():
    # Denominators that share no common factor: the lcm is their product, so
    # each numerator must be scaled by the OTHER denominator.
    assert add(Fraction(1, 5), Fraction(1, 7)) == Fraction(12, 35)
    assert add(Fraction(3, 8), Fraction(1, 3)) == Fraction(17, 24)


def test_add_returns_canonical_denominator():
    # 1/6 + 1/3 == 1/2, so the result denominator must reduce to 2, not stay
    # at the naive common multiple.
    result = add(Fraction(1, 6), Fraction(1, 3))
    assert (result.num, result.den) == (1, 2)
