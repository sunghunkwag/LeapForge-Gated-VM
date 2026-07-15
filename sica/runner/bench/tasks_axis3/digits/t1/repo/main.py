from helpers import mix


def encode(n):
    """Scramble a number into its stored code using the project's mixing step.

    ``n`` is a non-negative integer in range and the returned code is an
    integer. ``encode`` is correct and must not need changing.
    """
    return mix(n)


def unmix(raw):
    """Recover the original number from its stored code.

    ``unmix`` is meant to be the exact inverse of :func:`encode`, so that
    ``unmix(encode(n)) == n`` for every number ``n`` in range. It currently
    removes the offset and undoes the spreading by plain division, but that
    does not account for the wrap the mixing step applies, so it does not
    return the original number for every input.
    """
    base = mix(0)
    step = mix(1) - mix(0)
    return (raw - base) // step


def decode(raw):
    """Recover the original number from its stored code (see :func:`unmix`)."""
    return unmix(raw)
