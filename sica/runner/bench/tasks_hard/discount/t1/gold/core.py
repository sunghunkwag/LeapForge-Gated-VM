from tiers import TIER_DISCOUNT

def net(amount, tier):
    return round(amount * (1 - TIER_DISCOUNT[tier]), 2)
