_TO_M = {'mm': 0.001, 'm': 1.0, 'km': 1000.0}

def convert(x, frm, to):
    return x * _TO_M[frm] / _TO_M[to]
