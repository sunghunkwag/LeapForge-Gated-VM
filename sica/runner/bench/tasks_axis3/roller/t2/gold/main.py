"""Rolling-window sums over a list of numbers."""

from helpers import window


def window_sums(data, k):
    """Return the sum of every contiguous window of length ``k`` in ``data``,
    scanning left to right.

    ``data`` is a list of numbers and ``k`` is a positive integer. For
    ``data = [1, 2, 3, 4]`` and ``k = 2`` the result is ``[3, 5, 7]``; for
    ``k = 1`` it is ``[1, 2, 3, 4]``. When ``k`` equals ``len(data)`` there is
    a single window, so the result is a one-element list. When ``k`` is larger
    than ``len(data)`` there are no windows and the result is an empty list.
    """
    out = []
    for i in range(len(data) - k + 1):
        out.append(sum(window(data, i, k)))
    return out
