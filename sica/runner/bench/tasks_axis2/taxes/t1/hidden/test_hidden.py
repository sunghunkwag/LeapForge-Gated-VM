from main import receipt_net


def test_taxable_prices_strip_tax_once():
    # A gross that includes 10% tax comes back as the pre-tax net, with the
    # tax removed exactly once.
    assert receipt_net(110) == 100
    assert receipt_net(220) == 200
    assert receipt_net(550) == 500
    assert receipt_net(1100) == 1000


def test_taxable_prices_that_divide_evenly():
    assert receipt_net(121) == 110
    assert receipt_net(165) == 150
    assert receipt_net(330) == 300


def test_taxable_price_with_flooring():
    # 105 gross: the contained tax floors to 10, leaving a net of 95.
    assert receipt_net(105) == 95


def test_exempt_prices_unchanged():
    assert receipt_net(0) == 0
    assert receipt_net(1) == 1
    assert receipt_net(75) == 75
    assert receipt_net(100) == 100


def test_returns_integer():
    assert isinstance(receipt_net(110), int)
    assert isinstance(receipt_net(50), int)
