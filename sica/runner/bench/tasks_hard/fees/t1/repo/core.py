def fee(method, amount):
    if method == 'wire':
        return 20.0
    if method == 'ach':
        return 1.0
    return round(amount * 0.03, 2)
