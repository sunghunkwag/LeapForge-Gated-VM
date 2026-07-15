from core import convert

def test_public():
    assert convert(5,'m','m')==5
    assert convert(2000,'mm','m')==2
