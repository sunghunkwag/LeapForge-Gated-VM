from main import overlaps


def test_public():
    # Clearly overlapping intervals share many minutes.
    assert overlaps((0, 60), (30, 90)) is True
    assert overlaps((0, 100), (50, 60)) is True
    # Clearly separate intervals with a real gap between them do not overlap.
    assert overlaps((0, 60), (120, 180)) is False
    assert overlaps((0, 30), (60, 90)) is False
