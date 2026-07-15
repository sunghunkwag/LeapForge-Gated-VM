"""intervals: inserting a closed interval into a sorted, disjoint list.

An interval is a two-element ``[start, end]`` pair with ``start <= end`` and
both endpoints included (a *closed* interval), so ``[1, 3]`` and ``[3, 5]``
touch at the point ``3`` and are treated as overlapping.
"""


def insert(intervals, new):
    """Insert closed interval ``new`` = ``[start, end]`` into ``intervals``.

    ``intervals`` is a list of ``[start, end]`` pairs that are already sorted by
    start and pairwise disjoint (non-overlapping and non-touching).  Any
    existing intervals that overlap or touch ``new`` are absorbed into a single
    combined interval.  A new sorted, disjoint list is returned; the input is
    left unmodified.
    """
    start, end = new
    out = []
    i = 0
    n = len(intervals)
    # Intervals that end before ``new`` begins pass through untouched.
    while i < n and intervals[i][1] < start:
        out.append(list(intervals[i]))
        i += 1
    # Absorb every interval that overlaps or touches the inserted one.
    while i < n and intervals[i][0] <= end:
        start = min(start, intervals[i][0])
        end = intervals[i][1]
        i += 1
    out.append([start, end])
    # The remaining intervals start after ``new`` ends.
    while i < n:
        out.append(list(intervals[i]))
        i += 1
    return out
