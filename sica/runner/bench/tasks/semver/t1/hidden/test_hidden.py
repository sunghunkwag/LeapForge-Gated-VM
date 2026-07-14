from core import compare

def test_hidden():
    assert compare('1.10.0','1.9.0')==1
    assert compare('1.2.0','1.10.0')==-1
    assert compare('0.0.9','0.0.10')==-1
