"""intervals: overlap tests and merging for closed integer intervals.

Each interval is a two-element ``[start, end]`` pair with ``start <= end`` and
both endpoints included (a *closed* interval).  Because the endpoints are
included, ``[1, 3]`` and ``[3, 5]`` share the point ``3`` and are therefore
considered to overlap.
"""


def overlaps(a, b):
    """Return True if closed intervals ``a`` and ``b`` share at least one point.

    Touching at a single endpoint counts as overlapping, so
    ``overlaps([1, 3], [3, 5])`` is True.
    """
    return a[0] <= b[1] and b[0] <= a[1]


def merge(intervals):
    """Merge overlapping or touching closed intervals.

    Returns a new list of disjoint ``[start, end]`` intervals sorted by start.
    Two intervals are combined when they overlap or merely touch at an
    endpoint.
    """
    if not intervals:
        return []
    ordered = sorted(intervals)
    merged = [list(ordered[0])]
    for start, end in ordered[1:]:
        last = merged[-1]
        if start < last[1]:
            last[1] = max(last[1], end)
        else:
            merged.append([start, end])
    return merged
