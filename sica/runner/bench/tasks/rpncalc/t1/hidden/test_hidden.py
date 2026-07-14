"""Hidden grading tests for rpncalc/t1.

For the non-commutative operators ``-`` and ``/`` the operand that appeared
earlier in the expression is the left-hand side.  These cases FAIL on the buggy
snapshot (which pops the operands in the wrong order and so evaluates the
reverse: ``3 - 5`` instead of ``5 - 3``) and PASS once ``evaluate`` restores
the correct operand order.  The commutative cases are re-checked to confirm the
fix does not regress ``+`` / ``*``.
"""

from core import evaluate


def test_subtraction_order():
    assert evaluate("5 3 -") == 2
    assert evaluate("10 4 -") == 6
    assert evaluate("3 5 -") == -2
    assert evaluate("0 4 -") == -4


def test_division_order():
    assert evaluate("20 4 /") == 5
    assert evaluate("7 2 /") == 3
    assert evaluate("100 9 /") == 11


def test_nested_order_sensitive():
    # (9 - 3) / 2 == 3
    assert evaluate("9 3 - 2 /") == 3
    # 2 * (3 - 4) == -2
    assert evaluate("2 3 4 - *") == -2
    # (8 / 2) - 1 == 3
    assert evaluate("8 2 / 1 -") == 3


def test_deeper_expression():
    # ((10 - 2) / 4) - 3 == -1
    assert evaluate("10 2 - 4 / 3 -") == -1


def test_commutative_still_correct():
    assert evaluate("3 4 +") == 7
    assert evaluate("6 7 *") == 42
    assert evaluate("2 3 + 4 *") == 20
