"""rpncalc: evaluate integer arithmetic in reverse Polish notation (no eval)."""

_OPERATORS = {"+", "-", "*", "/"}


def _intdiv(a, b):
    """Integer division truncating toward zero, so 7 / 2 == 3 and -7 / 2 == -3."""
    quotient = abs(a) // abs(b)
    if (a < 0) != (b < 0):
        quotient = -quotient
    return quotient


def evaluate(expression):
    """Evaluate a reverse-Polish ``expression`` and return an integer.

    ``expression`` is a whitespace-separated string of integer operands and the
    binary operators ``+``, ``-``, ``*`` and ``/``.  Each operator pops the two
    most recently pushed values and pushes its result.  For the non-commutative
    ``-`` and ``/`` the operand that appeared EARLIER in the expression is the
    left-hand side, so ``"5 3 -"`` means ``5 - 3 == 2`` and ``"20 4 /"`` means
    ``20 / 4 == 5``.  Division is integer division that truncates toward zero.
    """
    stack = []
    for token in expression.split():
        if token in _OPERATORS:
            b = stack.pop()
            a = stack.pop()
            if token == "+":
                stack.append(a + b)
            elif token == "-":
                stack.append(a - b)
            elif token == "*":
                stack.append(a * b)
            else:
                stack.append(_intdiv(a, b))
        else:
            stack.append(int(token))
    return stack.pop()
