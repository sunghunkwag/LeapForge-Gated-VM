from core import can

def test_hidden():
    assert can('editor', 5) is True
    assert can('member', 3) is False
    assert can('admin', 9) is True
    assert can('guest', 1) is False
