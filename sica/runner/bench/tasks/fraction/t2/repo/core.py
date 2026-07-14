"""fraction: minimal rational-number arithmetic kept in lowest terms."""

from math import gcd


class Fraction:
    """A rational number stored in lowest terms with a positive denominator.

    The sign is always carried by the numerator, so two fractions that denote
    the same value compare equal -- for example Fraction(1, -2) equals
    Fraction(-1, 2), and both reduce to num=-1, den=2.
    """

    def __init__(self, numerator, denominator=1):
        if denominator == 0:
            raise ZeroDivisionError("denominator must be non-zero")
        if denominator < 0:
            numerator = -numerator
            denominator = -denominator
        g = gcd(abs(numerator), denominator) or 1
        self.num = numerator // g
        self.den = denominator // g

    def __eq__(self, other):
        return self.num == other.num and self.den == other.den

    def __hash__(self):
        return hash((self.num, self.den))

    def __repr__(self):
        return "Fraction(%d, %d)" % (self.num, self.den)


def add(a, b):
    """Return the reduced sum ``a + b``.

    Both fractions are put over the least common multiple of their
    denominators, then their scaled numerators are combined.
    """
    lcm = a.den // gcd(a.den, b.den) * b.den
    num = a.num * (lcm // a.den) + b.num * (lcm // a.den)
    return Fraction(num, lcm)


def compare(a, b):
    """Return -1, 0, or 1 as ``a`` is less than, equal to, or greater than
    ``b``."""
    left = a.num * b.den
    right = b.num * a.den
    if left < right:
        return -1
    if left > right:
        return 1
    return 0
