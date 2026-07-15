from core import apply_coupon

def test_hidden():
    assert apply_coupon(100, 10) == 90.0
    assert apply_coupon(50, 20) == 40.0
