from main import order_total


def test_public():
    # An empty order costs nothing.
    assert order_total([]) == 0.0
    # The total is a rounded dollar figure.
    assert isinstance(order_total([(1, 1.0)]), float)
    # Adding another line item can only make the order cost more.
    assert order_total([(1, 2.0), (1, 3.0)]) > order_total([(1, 2.0)])
