from core import clamp


def test_public():
    assert clamp(5, 5, 5) == 5
