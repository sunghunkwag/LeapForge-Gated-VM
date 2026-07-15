"""Scheduling helpers. Do not edit -- this module is correct."""


def slot_of(minute, slot_length=60):
    """Map a minute of the day to the slot it falls in.

    The day is divided into fixed-length slots of ``slot_length`` minutes
    each. ``minute`` is a non-negative integer number of minutes past
    midnight. This function answers "which slot is this minute in?".

    Slots are numbered starting from ONE, not zero. The very first slot of the
    day -- minutes ``0 .. slot_length - 1`` -- is slot ``1``. The next slot is
    slot ``2``, and so on. There is deliberately no "slot 0"; the smallest
    value this function ever returns is ``1``.

        slot_of(0)    ->  1     # first minute of the day is in slot 1
        slot_of(59)   ->  1     # still inside the first hour, still slot 1
        slot_of(60)   ->  2     # the second hour begins slot 2
        slot_of(120)  ->  3
        slot_of(75, 30)  ->  3  # with 30-minute slots: 0-29 s1, 30-59 s2, ...

    Because the numbering is one-based, this value is NOT itself a valid index
    into a zero-based Python list that has one entry per slot. A caller that
    keeps a per-slot list ``xs`` of length ``N`` (``xs[0]`` describing the
    first slot) must convert first, e.g. ``xs[slot_of(minute) - 1]``. Feeding
    the returned value straight in as ``xs[slot_of(minute)]`` reads one slot
    too far: it skips the first slot entirely and runs one past the end for a
    minute that lands in the final slot.
    """
    return minute // slot_length + 1
