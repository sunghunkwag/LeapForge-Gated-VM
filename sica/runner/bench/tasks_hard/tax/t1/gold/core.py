from rates import RATES

def taxed(price, category):
    return round(price * (1 + RATES[category]), 2)
