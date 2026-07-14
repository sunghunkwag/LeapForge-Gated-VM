from core import price

def test_hidden():
    assert price(0) == 4.25
    assert price(1) == 5.95
    assert price(2, True) == 6.5
