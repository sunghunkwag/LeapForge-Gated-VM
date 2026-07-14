from core import score

def test_hidden():
    assert score(3, 2, 1) == 12
    assert score(5, 0, 2) == 16
    assert score(0, 0, 4) == -8
