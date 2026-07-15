from core import cost

def test_hidden():
    assert cost(4, 10) == 15.5
    assert cost(0, 74.99) == 6.5
    assert cost(10, 75) == 0.0
