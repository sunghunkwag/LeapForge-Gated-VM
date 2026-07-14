def back(y):
    """Step a value back to recover the position it came from.

    ``back`` is meant to be the exact inverse of the project's forward step
    (``fwd`` in helpers.py, which is correct and must not change): for every
    position ``x`` in the documented domain, ``back(fwd(x))`` should return
    ``x``. It currently steps back by a single fixed amount, which does not
    undo a forward step whose size depends on the position, so the round-trip
    does not recover the original position.
    """
    return y - 2
