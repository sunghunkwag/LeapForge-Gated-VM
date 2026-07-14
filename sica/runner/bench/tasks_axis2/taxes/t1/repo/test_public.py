from main import receipt_net


def test_public():
    # Tax-exempt purchases (100 cents or less) carry no tax, so the net
    # equals the gross unchanged.
    assert receipt_net(0) == 0
    assert receipt_net(50) == 50
    assert receipt_net(99) == 99
    # The exemption reaches all the way up to 100 cents inclusive.
    assert receipt_net(100) == 100
    # The net comes back as an integer number of cents.
    assert isinstance(receipt_net(50), int)
