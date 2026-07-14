from core import mode

def test_public():
    assert mode([5])==5
    assert mode([7,7,7])==7
