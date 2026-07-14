from core import reachable

def test_hidden():
    assert reachable([[0,0],[0,0]]) is True
    assert reachable([[0,1],[1,0]]) is False
    assert reachable([[0,0,0],[1,1,0],[0,0,0]]) is True
