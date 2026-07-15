from core import clamp

def test_hidden():
    assert clamp(-3, 0, 10) == 0
    assert clamp(20, 0, 10) == 10
