from core import price

def test_public():
    assert isinstance(price(1), float)
    assert price(3) > price(1)
