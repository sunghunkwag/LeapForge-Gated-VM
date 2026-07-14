from helpers import span


def steps_between(low, high):
    """Return the number of integer step positions from ``low`` to ``high``.

    Walking from ``low`` up to ``high`` one unit at a time visits every
    integer position in between, counting both endpoints, so the result is an
    inclusive count of positions.
    """
    return span(low, high) + 1
