from schedule import WIRE_FLAT, ACH_FLAT, CARD_PCT

def fee(method, amount):
    if method == 'wire':
        return WIRE_FLAT
    if method == 'ach':
        return ACH_FLAT
    return round(amount * CARD_PCT, 2)
