from core import to_roman

def test_public():
    assert to_roman(1)=='I'
    assert to_roman(3)=='III'
    assert to_roman(10)=='X'
