from core import shortest

def test_hidden():
    assert shortest([[0,0],[0,0]])==2
    assert shortest([[0]])==0
    assert shortest([[0,0,0],[1,1,0],[0,0,0]])==4
