def overlaps(a, b):
    """Return True if two half-open time intervals overlap.

    Each interval is a ``(start, end)`` pair of integer minutes with
    ``start < end`` and represents the half-open range ``[start, end)`` -- it
    includes ``start`` but not ``end``. Two intervals overlap when they share
    at least one minute. Intervals that merely touch at an endpoint -- one ends
    exactly where the next begins, such as ``(0, 60)`` and ``(60, 120)`` -- do
    NOT overlap, because the shared instant ``60`` belongs to neither half-open
    range.
    """
    a_start, a_end = a
    b_start, b_end = b
    return a_start <= b_end and b_start <= a_end
