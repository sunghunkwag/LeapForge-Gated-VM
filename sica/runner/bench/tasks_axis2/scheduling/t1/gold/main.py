from helpers import slot_of


def capacity_at(minute, capacities, slot_length=60):
    """Return the scheduled capacity for the slot a given minute falls in.

    ``capacities`` is a list holding one capacity per slot, in slot order.
    ``minute`` is a non-negative integer number of minutes past midnight. The
    minute-to-slot mapping is delegated to ``slot_of`` (imported from
    ``helpers``); this function then reads the matching entry out of
    ``capacities`` and returns it.
    """
    return capacities[slot_of(minute, slot_length) - 1]
