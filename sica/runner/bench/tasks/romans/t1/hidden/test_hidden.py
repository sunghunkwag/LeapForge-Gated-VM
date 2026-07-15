from core import to_roman

def test_hidden():
    assert to_roman(4)=='IV'
    assert to_roman(9)=='IX'
    assert to_roman(40)=='XL'
    assert to_roman(1994)=='MCMXCIV'
