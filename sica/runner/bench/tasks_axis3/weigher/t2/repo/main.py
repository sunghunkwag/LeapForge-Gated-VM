from helpers import combine


def remaining_capacity(limit, loads):
    """Return how much more weight can still be added to a scale.

    ``limit`` is the scale's maximum weight and ``loads`` is a list of the
    weights already on the scale. The remaining capacity is the limit minus
    everything already loaded, so an empty scale has its full limit remaining
    and a scale loaded exactly to the limit has zero remaining.
    """
    used = 0
    for w in loads:
        used = combine(used, w)
    return limit + used
