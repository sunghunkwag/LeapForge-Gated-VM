from helpers import compute


def receipt_net(price):
    """Return the net (pre-tax) amount for a tax-inclusive gross ``price``.

    ``price`` is a gross amount in integer cents that includes any applicable
    sales tax. Returns the underlying pre-tax amount in integer cents.
    """
    base = compute(price)
    tax = price - base            # the sales tax contained in the gross price
    return base - tax             # take the tax off to reach the net amount
