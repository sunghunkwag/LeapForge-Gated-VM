import math

from helpers import rotate


def rotate_point(pt, degrees):
    """Rotate the point ``pt`` counter-clockwise about the origin.

    ``pt`` is an ``(x, y)`` pair. ``degrees`` is the amount to rotate by,
    measured in degrees, so ``90`` is a quarter turn and ``180`` is a half
    turn. Returns the rotated point as an ``(x, y)`` tuple of floats.
    """
    return rotate(pt, math.radians(degrees))
