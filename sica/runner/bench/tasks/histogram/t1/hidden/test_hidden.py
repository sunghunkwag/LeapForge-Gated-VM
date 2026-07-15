from core import mode

def test_hidden():
    assert mode([1,1,2])==1
    assert mode([3,3,3,4])==3
    assert mode([9,8,8])==8
