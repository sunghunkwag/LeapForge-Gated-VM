"""Planar geometry primitives. Do not edit -- this module is correct."""

import math


def rotate(pt, angle):
    """Rotate the point ``pt`` counter-clockwise about the origin.

    ``pt`` is an ``(x, y)`` pair. ``angle`` is the amount to turn by, and it is
    consumed as a plain radian measure: the value is handed straight to
    ``math.cos`` and ``math.sin``, whose argument is itself an angle in
    radians. A quarter turn is therefore ``math.pi / 2`` (about 1.5708), a half
    turn is ``math.pi``, and a full turn is ``2 * math.pi`` -- not 90, 180 and
    360.

    Because of that, feeding this function a whole-circle count in degree units
    spins the point by that many radians instead. The number 90, for instance,
    is read here as an angle of roughly 5157 degrees, so the point comes back in
    the wrong place. Any caller that is holding its angle in degree units has to
    scale it into radian units first -- ``math.radians(deg)`` or
    ``deg * math.pi / 180`` -- before handing it over.

    Returns the rotated point as an ``(x, y)`` tuple of floats. The distance of
    the point from the origin is preserved for any angle.

        rotate((1.0, 0.0), math.pi / 2)  ->  (0.0, 1.0)   # a quarter turn
    """
    x, y = pt
    c = math.cos(angle)
    s = math.sin(angle)
    return (x * c - y * s, x * s + y * c)
