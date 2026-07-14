from core import percent

def test_hidden():
    assert percent(1, 4) == 25.0
    assert percent(3, 5) == 60.0
