from main import fulfill


def test_exact_stock_order_leaves_zero():
    # Reserving the entire remaining stock is a valid, fillable order that
    # leaves zero units behind -- it must not be reported as unfillable.
    assert fulfill(4, 4) == 0
    assert fulfill(1, 1) == 0
    assert fulfill(50, 50) == 0


def test_oversized_order_is_unfillable_not_a_crash():
    # An order larger than the stock on hand cannot be met and must be
    # reported as None rather than raising.
    assert fulfill(3, 5) is None
    assert fulfill(0, 1) is None
    assert fulfill(9, 100) is None


def test_partial_orders_return_remaining_stock():
    assert fulfill(10, 3) == 7
    assert fulfill(8, 0) == 8
    assert fulfill(7, 2) == 5
