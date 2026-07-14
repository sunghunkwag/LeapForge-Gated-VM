"""Public regression guard for rpncalc/t1.

Every assertion here already holds on the shipped code.  They cover the
commutative operators (``+`` and ``*``), single operands, and only those
``-`` / ``/`` cases whose two operands are equal -- for which operand order
cannot matter.  The reported order bug only shows up when the two operands of
a ``-`` or ``/`` differ, so none of these are affected; they guard the parse /
dispatch / nesting paths against being broken by a fix.
"""

from core import evaluate


def test_single_operand():
    assert evaluate("42") == 42
    assert evaluate("-7") == -7


def test_addition():
    assert evaluate("3 4 +") == 7
    assert evaluate("10 20 +") == 30


def test_multiplication():
    assert evaluate("3 4 *") == 12
    assert evaluate("5 6 *") == 30


def test_nested_commutative():
    assert evaluate("2 3 + 4 *") == 20
    assert evaluate("2 3 4 + +") == 9
    assert evaluate("2 3 4 * *") == 24


def test_equal_operand_subtraction_and_division():
    # Both operands equal, so which one is the left-hand side is irrelevant.
    assert evaluate("5 5 -") == 0
    assert evaluate("4 4 /") == 1
