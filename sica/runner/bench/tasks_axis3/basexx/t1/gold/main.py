from helpers import enc


def encode(n):
    """Encode a non-negative integer ``n`` into its stored code string.

    ``encode`` is correct and relies on the project's encoding step; it must
    not need changing.
    """
    return enc(n)


def dec(code):
    """Turn a stored code string back into the integer it stands for.

    ``dec`` is the exact inverse of :func:`encode`, so that
    ``dec(encode(n)) == n`` for every non-negative integer ``n``. The code is
    read as a positional number: the letters are combined from the most
    significant end, and each letter contributes the digit given by its
    position in the project's own letter alphabet -- not by treating the
    letters as a plain run.
    """
    alphabet = "GTPWABK"
    base = len(alphabet)
    value = 0
    for ch in code:
        value = value * base + alphabet.index(ch)
    return value


def decode(code):
    """Recover the original integer from a stored code (see :func:`dec`)."""
    return dec(code)
