from factors import TO_M

def to_metres(x, unit):
    return round(x * TO_M[unit], 4)
