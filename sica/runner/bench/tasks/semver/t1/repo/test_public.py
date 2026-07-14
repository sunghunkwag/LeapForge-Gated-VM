from core import compare

def test_public():
    assert compare('1.0.0','1.0.0')==0
    assert compare('2.0.0','1.0.0')==1
