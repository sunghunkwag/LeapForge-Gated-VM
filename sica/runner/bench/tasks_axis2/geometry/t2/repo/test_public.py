from main import point_in_rect


def test_public():
    # Strictly interior points are inside.
    assert point_in_rect(5, 5, 0, 0, 10, 10) is True
    assert point_in_rect(1, 1, 0, 0, 10, 10) is True
    assert point_in_rect(9, 2, 0, 0, 10, 10) is True

    # Points well outside the rectangle are outside.
    assert point_in_rect(15, 5, 0, 0, 10, 10) is False
    assert point_in_rect(-1, 5, 0, 0, 10, 10) is False
    assert point_in_rect(5, 20, 0, 0, 10, 10) is False
    assert point_in_rect(5, -3, 0, 0, 10, 10) is False
