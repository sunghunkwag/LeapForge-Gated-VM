"""Hidden grading tests for rpncalc/t2.

Integer division must truncate the fractional part toward zero, so a quotient
with exactly one negative operand rounds up toward zero rather than down.
These cases FAIL on the buggy snapshot (which uses Python's floor division and
so rounds negative quotients away from zero, e.g. -7 / 2 -> -4) and PASS once
division truncates toward zero.  Positive, exact and same-sign divisions are
re-checked to confirm the fix does not regress them.
"""

from core import evaluate


def test_negative_dividend_truncates_toward_zero():
    assert evaluate("-7 2 /") == -3
    assert evaluate("-1 2 /") == 0
    assert evaluate("-9 4 /") == -2
    assert evaluate("-100 7 /") == -14


def test_negative_divisor_truncates_toward_zero():
    assert evaluate("7 -2 /") == -3
    assert evaluate("1 -2 /") == 0
    assert evaluate("9 -4 /") == -2
    assert evaluate("100 -7 /") == -14


def test_nested_negative_division():
    # (0 - 7) / 2 == -3   (floor would give -4)
    assert evaluate("0 7 - 2 /") == -3
    # (3 - 10) / 3 == -2   (floor would give -3)
    assert evaluate("3 10 - 3 /") == -2


def test_positive_and_exact_unaffected():
    assert evaluate("20 4 /") == 5
    assert evaluate("7 2 /") == 3
    assert evaluate("-8 2 /") == -4
    assert evaluate("-7 -2 /") == 3
