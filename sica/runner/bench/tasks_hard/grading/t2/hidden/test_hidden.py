from core import average

def test_hidden():
    assert average([1, 2]) == 1.5
    assert average([1, 2, 2]) == 5/3
