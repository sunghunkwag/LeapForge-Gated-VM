from core import allowed

def test_hidden():
    assert allowed('free', 29) is True
    assert allowed('free', 30) is False
    assert allowed('pro', 299) is True
    assert allowed('enterprise', 5000) is False
