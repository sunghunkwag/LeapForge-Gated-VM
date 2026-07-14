from helpers import line_total


def order_total(items):
    """Return the total cost of an order, in dollars.

    ``items`` is a list of ``(qty, unit_price)`` pairs, where ``unit_price`` is
    a price in dollars. The result is rounded to the nearest cent.
    """
    total_cents = 0
    for qty, unit_price in items:
        total_cents += line_total(qty, unit_price)
    return round(total_cents / 100.0, 2)
