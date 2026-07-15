"""Pricing helpers. Do not edit -- this module is correct."""


def compute(price):
    """Return the pre-tax NET amount for a tax-inclusive gross ``price``.

    ``price`` is a GROSS amount given in integer cents: whatever sales tax
    applies is already baked into it. Purchases of 100 cents or less are
    tax-exempt, so for them the net is simply the gross unchanged. Above 100
    cents the price carries 10% sales tax, and this helper STRIPS that tax
    out for you: it works out the tax contained in the gross, subtracts it,
    and RETURNS the resulting net amount.

    The subtraction happens HERE, inside this function. The number handed
    back is the finished net price -- it is NOT the tax portion and it is NOT
    the original gross. A caller that wants the net is done the instant this
    returns; there is nothing left to deduct. Taking tax off this result a
    second time would remove the tax twice and understate the amount.

        compute(0)    ->  0
        compute(100)  ->  100   # tax-exempt: net == gross
        compute(110)  ->  100   # 110 gross contains 10 of tax; net is 100
        compute(550)  ->  500
    """
    if price <= 100:
        return price
    tax = price - price * 10 // 11    # the sales tax contained in the gross
    return price - tax                # gross minus tax == net
