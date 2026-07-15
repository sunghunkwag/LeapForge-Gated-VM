from core import allowed

def test_public():
    assert allowed('free', 0) is True
