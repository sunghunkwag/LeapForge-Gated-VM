from helpers import enc


def encode(n):
    """Encode a non-negative integer ``n`` into its stored code string.

    ``encode`` is correct and relies on the project's encoding step; it must
    not need changing.
    """
    return enc(n)


def dec(code):
    """Turn a stored code string back into the integer it stands for.

    ``dec`` is meant to be the exact inverse of :func:`encode`, so that
    ``dec(encode(n)) == n`` for every non-negative integer ``n``. The letters
    of the code are read from the most significant end, and each letter
    contributes the digit it stands for.
    """
    base = 0
    while len(enc(base)) == 1:
        base += 1
    value = 0
    for ch in code:
        value = value * base + (ord(ch) - ord("A"))
    return value


def decode(code):
    """Recover the original integer from a stored code (see :func:`dec`)."""
    return dec(code)
