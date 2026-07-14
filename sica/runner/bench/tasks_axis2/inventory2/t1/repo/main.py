from helpers import reserve


def fulfill(stock, order):
    """Fulfil an order for ``order`` units drawn from ``stock``.

    Return the number of units remaining in stock once the order has been
    filled, or ``None`` when the order cannot be met.
    """
    if not reserve(stock, order):
        return None
    return stock - order
