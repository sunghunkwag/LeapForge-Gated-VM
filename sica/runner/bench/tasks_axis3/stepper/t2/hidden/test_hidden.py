from main import steps_between


def test_inclusive_counts():
    assert steps_between(0, 5) == 6
    assert steps_between(2, 6) == 5
    assert steps_between(1, 10) == 10


def test_single_position():
    assert steps_between(0, 0) == 1
    assert steps_between(5, 5) == 1


def test_negative_positions():
    assert steps_between(-3, 3) == 7
    assert steps_between(-10, -4) == 7
