from core import cheapest

def test_hidden():
    assert cheapest([5, 2, 9]) == 2
    assert cheapest([3, 3, 1]) == 1
