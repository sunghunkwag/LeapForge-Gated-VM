"""Sequence-search utilities. Do not edit -- this module is correct."""


def find_index(seq, x):
    """Return the 0-based index of the first element of ``seq`` equal to ``x``.

    Miss convention: when ``x`` is absent this returns the sentinel ``-1``,
    NEVER ``None``. ``-1`` is a real, non-None ``int``, chosen so a caller can
    still tell "found at position 0" apart from "absent". Because a miss is
    signalled by ``-1``, callers MUST detect a miss by comparing the result
    against ``-1`` (e.g. ``if idx == -1``); testing ``if idx is None`` is a
    bug -- this function never yields ``None``.
    """
    for i, item in enumerate(seq):
        if item == x:
            return i
    return -1   # miss -> sentinel -1, not None
