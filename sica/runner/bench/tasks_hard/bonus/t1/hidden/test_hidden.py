from core import bonus

def test_hidden():
    assert bonus(1000) == 120.0
    assert bonus(5000) == 500.0
    assert bonus(2000) == 240.0
