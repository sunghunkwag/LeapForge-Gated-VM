from main import clamp

def test_hidden():
    assert clamp(15,0,10)==10
