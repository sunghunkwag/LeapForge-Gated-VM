import math

from main import rotate_point


def test_public():
    # Rotating by zero degrees is a no-op (0 deg and 0 rad coincide, so the
    # angle-unit question cannot surface here).
    assert rotate_point((2.0, 3.0), 0) == (2.0, 3.0)

    # A rotation about the origin preserves the point's distance from the
    # origin, whatever unit the angle happens to be interpreted in.
    for deg in (30, 90, 180, 270):
        x, y = rotate_point((3.0, 4.0), deg)
        assert math.isclose(math.hypot(x, y), 5.0, rel_tol=1e-9)

    # The result is always an (x, y) pair of numbers.
    r = rotate_point((1.0, 0.0), 45)
    assert isinstance(r, tuple)
    assert len(r) == 2
