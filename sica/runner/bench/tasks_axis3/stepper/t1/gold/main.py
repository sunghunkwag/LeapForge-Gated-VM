from helpers import fwd


def back(y):
    """Step a value back to recover the position it came from.

    ``back`` is the exact inverse of the project's forward step (``fwd`` in
    helpers.py) over the documented domain, so that ``back(fwd(x)) == x`` for
    every position ``x`` in that domain. Because each position steps forward
    by an amount that depends on the position, ``back`` recovers the original
    by finding, over the documented domain, the unique position whose forward
    step yields ``y``.
    """
    for x in range(50):
        if fwd(x) == y:
            return x
    raise ValueError(y)
