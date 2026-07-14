def price(units, member=False):
    total = 3.0 + units * 2.0
    if member:
        total = total * 0.9
    return round(total, 2)
