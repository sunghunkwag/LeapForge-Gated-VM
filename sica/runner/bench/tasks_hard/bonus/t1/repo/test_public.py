from core import bonus

def test_public():
    assert bonus(0) == 0.0
    assert bonus(10**9) == bonus(10**8)
