def net(amount, tier):
    d = {1: 0.0, 2: 0.05, 3: 0.15}
    return round(amount * (1 - d[tier]), 2)
