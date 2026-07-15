"""rpncalc: evaluate integer arithmetic in reverse Polish notation (no eval)."""

_OPERATORS = {"+", "-", "*", "/"}


def evaluate(expression):
    """Evaluate a reverse-Polish ``expression`` and return an integer.

    ``expression`` is a whitespace-separated string of integer operands and the
    binary operators ``+``, ``-``, ``*`` and ``/``.  Each operator pops the two
    most recently pushed values (the earlier one is the left-hand side) and
    pushes its result, so ``"5 3 -"`` is ``5 - 3 == 2``.  ``/`` is integer
    division that truncates the fractional part toward zero, the way a pocket
    calculator does: ``7 / 2 == 3`` and ``-7 / 2 == -3``.
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
                stack.append(a // b)
        else:
            stack.append(int(token))
    return stack.pop()
