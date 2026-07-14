from helpers import find_index


def index_of(seq, x, default=None):
    """Return the 0-based index of ``x`` in ``seq``, or ``default`` if absent."""
    idx = find_index(seq, x)
    if idx is None:
        return default
    return idx


def contains(seq, x):
    """Return True iff ``x`` is present in ``seq``."""
    return find_index(seq, x) is not None
