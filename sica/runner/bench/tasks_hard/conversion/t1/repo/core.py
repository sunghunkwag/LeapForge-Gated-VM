def to_metres(x, unit):
    f = {'mi': 1600.0, 'ft': 0.3, 'yd': 0.9}
    return round(x * f[unit], 4)
