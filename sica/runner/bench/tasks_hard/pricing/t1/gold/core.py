from rules import BASE_FEE, PER_UNIT, MEMBER_DISCOUNT

def price(units, member=False):
    total = BASE_FEE + units * PER_UNIT
    if member:
        total = total * (1 - MEMBER_DISCOUNT)
    return round(total, 2)
