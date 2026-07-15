def point_in_rect(px, py, x0, y0, x1, y1):
    """Return True if the point ``(px, py)`` lies within the axis-aligned
    rectangle whose opposite corners are ``(x0, y0)`` and ``(x1, y1)``.

    The rectangle is INCLUSIVE of its boundary: a point sitting exactly on any
    edge or corner counts as inside. Assumes ``x0 <= x1`` and ``y0 <= y1``.
    """
    return x0 <= px <= x1 and y0 <= py <= y1
