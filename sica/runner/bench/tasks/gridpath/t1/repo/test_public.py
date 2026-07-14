from core import shortest

def test_public():
    assert shortest([[1,0],[0,0]])==-1
    assert shortest([[0,1],[1,0]])==-1
