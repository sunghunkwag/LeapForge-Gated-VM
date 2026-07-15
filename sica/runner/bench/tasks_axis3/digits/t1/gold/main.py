from helpers import mix


def encode(n):
    """Scramble a number into its stored code using the project's mixing step.

    ``n`` is a non-negative integer in range and the returned code is an
    integer. ``encode`` is correct and must not need changing.
    """
    return mix(n)


def unmix(raw):
    """Recover the original number from its stored code.

    ``unmix`` is the exact inverse of :func:`encode`: it removes the offset the
    mixing step added and undoes the spreading with modular arithmetic, so the
    wrap the mixing step applies is reversed and ``unmix(encode(n)) == n`` for
    every number ``n`` in range.
    """
    base = mix(0)
    return ((raw - base) * 667) % 1000


def decode(raw):
    """Recover the original number from its stored code (see :func:`unmix`)."""
    return unmix(raw)
