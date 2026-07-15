from helpers import total


def scaled_sum(values, factor):
    """Scale every value in ``values`` by ``factor`` and return the total."""
    scaled = []
    for v in values:
        scaled.append(v + factor)
    return total(scaled)
