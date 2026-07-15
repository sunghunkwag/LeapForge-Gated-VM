from core import from_roman

def test_hidden():
    assert from_roman('IV')==4
    assert from_roman('IX')==9
    assert from_roman('XL')==40
    assert from_roman('MCMXCIV')==1994
