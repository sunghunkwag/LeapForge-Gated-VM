def apply_coupon(total, pct):
    return round(total - total * pct / 100.0, 2)
