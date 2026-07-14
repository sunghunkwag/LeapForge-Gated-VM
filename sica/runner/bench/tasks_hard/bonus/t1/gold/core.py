from plan import BONUS_RATE, BONUS_CAP

def bonus(sales):
    return min(sales * BONUS_RATE, BONUS_CAP)
