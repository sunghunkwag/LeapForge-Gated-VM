def penalty(days_late):
    return min(days_late * 2.0, 15.0)
