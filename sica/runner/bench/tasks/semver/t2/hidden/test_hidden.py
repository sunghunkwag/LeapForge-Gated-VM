from core import is_valid

def test_hidden():
    assert is_valid('1.0.0-rc.1') is True
    assert is_valid('2.3.4-alpha') is True
    assert is_valid('1.0.0-') is False
