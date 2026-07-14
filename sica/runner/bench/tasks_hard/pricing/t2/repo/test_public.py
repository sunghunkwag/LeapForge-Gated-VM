from core import apply_coupon

def test_public():
    assert apply_coupon(100, 0) == 100
