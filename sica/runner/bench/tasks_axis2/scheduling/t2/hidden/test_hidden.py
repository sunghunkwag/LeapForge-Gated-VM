from main import overlaps


def test_touching_endpoints_do_not_overlap():
    assert overlaps((0, 60), (60, 120)) is False
    assert overlaps((60, 120), (0, 60)) is False
    assert overlaps((0, 30), (30, 60)) is False
    assert overlaps((100, 200), (200, 300)) is False


def test_genuinely_overlapping():
    assert overlaps((0, 60), (30, 90)) is True
    assert overlaps((10, 50), (20, 30)) is True   # second fully inside first
    assert overlaps((20, 30), (10, 50)) is True   # first fully inside second


def test_single_minute_of_overlap():
    # (0, 61) extends one minute into (60, 120): they share minute 60.
    assert overlaps((0, 61), (60, 120)) is True
    assert overlaps((60, 120), (0, 61)) is True


def test_disjoint_with_gap():
    assert overlaps((0, 30), (60, 90)) is False
    assert overlaps((100, 200), (0, 50)) is False
    assert overlaps((0, 10), (11, 20)) is False


def test_identical_intervals_overlap():
    assert overlaps((0, 60), (0, 60)) is True
    assert overlaps((5, 6), (5, 6)) is True
