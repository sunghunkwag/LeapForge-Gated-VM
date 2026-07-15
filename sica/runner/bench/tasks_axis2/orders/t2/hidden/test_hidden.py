from main import bulk_discount


def test_hidden():
    # Exactly 10 units is the threshold and must get the 10% discount.
    assert bulk_discount(10, 5.0) == 45.0
    assert bulk_discount(10, 1.0) == 9.0
    # Above the threshold still gets the discount.
    assert bulk_discount(11, 5.0) == 49.5
    assert bulk_discount(50, 2.0) == 90.0
    # Below the threshold pays full price.
    assert bulk_discount(9, 4.0) == 36.0
    assert bulk_discount(2, 4.0) == 8.0
