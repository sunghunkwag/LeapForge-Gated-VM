from core import top_k

def test_hidden():
    assert top_k([1,1,1,2,2,3],2)==[1,2]
    assert top_k([4,4,5,5,5],1)==[5]
