from core import can

def test_public():
    assert can('admin', 0) is True
    assert isinstance(can('guest', 1), bool)
