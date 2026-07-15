from core import penalty

def test_hidden():
    assert penalty(2) == 7.0
    assert penalty(4) == 14.0
    assert penalty(10) == 20.0
