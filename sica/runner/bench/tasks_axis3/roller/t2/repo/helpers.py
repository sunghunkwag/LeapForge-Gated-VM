"""Sequence helpers. Do not edit -- this module is correct."""


def window(seq, start, length):
    """Return the slice of ``seq`` of ``length`` items beginning at ``start``.

        window([1, 2, 3, 4], 1, 2)  ->  [2, 3]
    """
    return seq[start:start + length]
