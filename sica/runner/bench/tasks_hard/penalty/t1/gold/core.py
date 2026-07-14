from policy import LATE_PER_DAY, MAX_PENALTY

def penalty(days_late):
    return min(days_late * LATE_PER_DAY, MAX_PENALTY)
