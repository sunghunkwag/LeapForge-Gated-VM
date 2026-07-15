import math

from main import rotate_point


def _close(pt, ex, ey):
    x, y = pt
    assert math.isclose(x, ex, abs_tol=1e-9)
    assert math.isclose(y, ey, abs_tol=1e-9)


def test_quarter_turn():
    # 90 degrees takes the +x axis onto the +y axis.
    _close(rotate_point((1.0, 0.0), 90), 0.0, 1.0)
    # 90 degrees takes the +y axis onto the -x axis.
    _close(rotate_point((0.0, 1.0), 90), -1.0, 0.0)


def test_half_and_three_quarter_turns():
    _close(rotate_point((1.0, 0.0), 180), -1.0, 0.0)
    _close(rotate_point((1.0, 0.0), 270), 0.0, -1.0)
    _close(rotate_point((3.0, 4.0), 180), -3.0, -4.0)


def test_forty_five_degrees():
    h = math.sqrt(2.0) / 2.0
    _close(rotate_point((1.0, 0.0), 45), h, h)


def test_non_unit_point_quarter_turn():
    # (3, 4) rotated a quarter turn lands on (-4, 3).
    _close(rotate_point((3.0, 4.0), 90), -4.0, 3.0)


def test_full_turn_is_identity():
    _close(rotate_point((2.0, -5.0), 360), 2.0, -5.0)


def test_zero_is_identity():
    _close(rotate_point((7.0, -1.0), 0), 7.0, -1.0)
