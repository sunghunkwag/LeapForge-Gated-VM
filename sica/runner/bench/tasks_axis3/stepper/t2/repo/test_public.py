from main import steps_between


def test_steps_between_returns_int():
    assert isinstance(steps_between(0, 5), int)
    assert isinstance(steps_between(3, 3), int)


def test_steps_between_is_deterministic():
    assert steps_between(1, 4) == steps_between(1, 4)
