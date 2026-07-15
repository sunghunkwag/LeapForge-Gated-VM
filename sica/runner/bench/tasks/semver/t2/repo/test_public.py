from core import is_valid

def test_public():
    assert is_valid('1.2.3') is True
    assert is_valid('1.2') is False
    assert is_valid('x.y.z') is False
