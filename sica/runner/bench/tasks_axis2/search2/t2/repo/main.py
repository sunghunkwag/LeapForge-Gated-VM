def count_in_range(nums, lo, hi):
    """Count how many values in ``nums`` lie within the INCLUSIVE range [lo, hi].

    A value ``n`` counts when ``lo <= n <= hi`` (both endpoints included).
    """
    c = 0
    for n in nums:
        if lo <= n < hi:
            c += 1
    return c
