"""Public regression guard for rpncalc/t2.

Every assertion here already holds on the shipped code.  The division cases use
only positive operands, exact divisions, or same-sign operands -- situations
where truncating toward zero and Python's floor division agree -- so the
reported rounding problem never surfaces here.  They guard the parse, dispatch,
operand order, and the +/-/* paths against being broken by a fix.
"""

from core import evaluate


def test_single_and_basic_ops():
    assert evaluate("42") == 42
    assert evaluate("3 4 +") == 7
    assert evaluate("5 3 -") == 2
    assert evaluate("6 7 *") == 42


def test_positive_division():
    assert evaluate("20 4 /") == 5
    assert evaluate("7 2 /") == 3
    assert evaluate("100 9 /") == 11


def test_exact_division_with_negatives():
    # No remainder, so truncation and flooring give the same result.
    assert evaluate("-8 2 /") == -4
    assert evaluate("9 -3 /") == -3


def test_same_sign_division():
    # Both operands negative: floor and truncate-toward-zero agree.
    assert evaluate("-7 -2 /") == 3
    assert evaluate("-9 -4 /") == 2


def test_nested_positive():
    # (12 / 3) + 1 == 5
    assert evaluate("12 3 / 1 +") == 5
