from core import subtotal

def test_hidden():
    assert subtotal([1, 2, 3]) == 6
    assert subtotal([5]) == 5
