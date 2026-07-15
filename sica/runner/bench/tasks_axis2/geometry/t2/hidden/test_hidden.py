from main import point_in_rect


def test_right_and_top_edges_are_inside():
    # Points exactly on the right/top edge are inside (inclusive rectangle).
    assert point_in_rect(10, 5, 0, 0, 10, 10) is True   # right edge
    assert point_in_rect(5, 10, 0, 0, 10, 10) is True   # top edge
    assert point_in_rect(10, 0, 0, 0, 10, 10) is True   # bottom-right corner
    assert point_in_rect(0, 10, 0, 0, 10, 10) is True   # top-left corner


def test_corners_are_inside():
    assert point_in_rect(0, 0, 0, 0, 10, 10) is True      # bottom-left
    assert point_in_rect(10, 10, 0, 0, 10, 10) is True    # top-right


def test_left_and_bottom_edges_are_inside():
    assert point_in_rect(0, 5, 0, 0, 10, 10) is True   # left edge
    assert point_in_rect(5, 0, 0, 0, 10, 10) is True   # bottom edge


def test_just_outside_edges_are_outside():
    assert point_in_rect(11, 5, 0, 0, 10, 10) is False
    assert point_in_rect(5, 11, 0, 0, 10, 10) is False
    assert point_in_rect(-1, -1, 0, 0, 10, 10) is False


def test_interior_still_inside():
    assert point_in_rect(5, 5, 0, 0, 10, 10) is True
    assert point_in_rect(3, 7, 0, 0, 10, 10) is True


def test_negative_coordinate_rectangle():
    # Boundary inclusion also holds for a rectangle spanning negatives.
    assert point_in_rect(2, 2, -2, -2, 2, 2) is True    # top-right corner
    assert point_in_rect(-2, 0, -2, -2, 2, 2) is True   # left edge
    assert point_in_rect(3, 0, -2, -2, 2, 2) is False   # outside right
