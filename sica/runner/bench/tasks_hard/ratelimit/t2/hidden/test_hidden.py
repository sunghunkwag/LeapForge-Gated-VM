from core import remaining

def test_hidden():
    assert remaining(10, 15) == 0
    assert remaining(5, 5) == 0
