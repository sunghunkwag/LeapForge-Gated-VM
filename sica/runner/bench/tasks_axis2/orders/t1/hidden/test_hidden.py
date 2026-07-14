from main import order_total


def test_hidden():
    # Totals must come back in dollars, not cents.
    assert order_total([(3, 2.5)]) == 7.5
    assert order_total([(2, 1.99)]) == 3.98
    assert order_total([(1, 10.0), (2, 2.5)]) == 15.0
    assert order_total([(4, 0.25)]) == 1.0
    assert order_total([(5, 1.0), (3, 2.0), (1, 0.5)]) == 11.5
    assert order_total([]) == 0.0
