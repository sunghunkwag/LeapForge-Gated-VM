from core import from_roman

def test_public():
    assert from_roman('III')==3
    assert from_roman('X')==10
    assert from_roman('MMVI')==2006
