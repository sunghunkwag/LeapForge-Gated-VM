from core import convert

def test_hidden():
    assert convert(1,'km','m')==1000
    assert convert(500,'m','km')==0.5
    assert convert(3,'km','mm')==3000000
