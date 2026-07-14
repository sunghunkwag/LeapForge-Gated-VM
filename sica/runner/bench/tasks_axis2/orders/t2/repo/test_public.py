from main import bulk_discount


def test_public():
    # Small orders pay full price.
    assert bulk_discount(1, 2.0) == 2.0
    assert bulk_discount(3, 5.0) == 15.0
    # Large orders (well above the threshold) get 10% off.
    assert bulk_discount(20, 1.0) == 18.0
