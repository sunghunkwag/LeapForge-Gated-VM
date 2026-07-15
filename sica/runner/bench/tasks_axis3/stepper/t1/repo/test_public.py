from main import back


def test_back_returns_int():
    assert isinstance(back(1), int)
    assert isinstance(back(5), int)
    assert isinstance(back(7), int)


def test_back_is_deterministic():
    assert back(4) == back(4)
    assert back(9) == back(9)
