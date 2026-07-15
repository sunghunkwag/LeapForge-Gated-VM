def bulk_discount(qty, unit_price):
    """Return the total price for an order of ``qty`` units.

    Orders of 10 or more units receive a 10% bulk discount. The result is
    rounded to the nearest cent.
    """
    total = qty * unit_price
    if qty > 10:
        total = total * 0.9
    return round(total, 2)
