from helpers import reserve


def fulfill(stock, order):
    """Fulfil an order for ``order`` units drawn from ``stock``.

    Return the number of units remaining in stock once the order has been
    filled, or ``None`` when the order cannot be met.
    """
    try:
        return reserve(stock, order)
    except ValueError:
        return None
