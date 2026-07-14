"""listalgo: small pure-Python list algorithms."""


def chunk(items, size):
    """Split ``items`` into consecutive sublists of length ``size``.

    The final chunk is shorter when ``len(items)`` is not a multiple of
    ``size``. ``size`` must be a positive integer.
    """
    if size <= 0:
        raise ValueError("size must be positive")
    result = []
    i = 0
    while i + size <= len(items):
        result.append(items[i:i + size])
        i += size
    return result


def dedup(items):
    """Return ``items`` with duplicates removed, keeping first-seen order."""
    seen = set()
    out = []
    for x in items:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def running_max(nums):
    """Return the running (cumulative) maximum of ``nums``."""
    out = []
    best = None
    for n in nums:
        if best is None or n > best:
            best = n
        out.append(best)
    return out
