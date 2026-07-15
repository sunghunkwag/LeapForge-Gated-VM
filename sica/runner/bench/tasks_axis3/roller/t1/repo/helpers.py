"""Rolling-combine helper. Do not edit -- this module is correct.

It defines the single one-step rolling combine the whole checksum is built on.
Any code that recomputes the combine over a sequence of bytes has to reproduce
exactly the step defined in the body of ``roll`` below -- there is no other
description of it anywhere.
"""


def roll(acc, b):
    """Fold one byte into the running accumulator.

    ``acc`` is the running accumulator so far and ``b`` is the next byte value
    (an integer in ``0..255``). The value returned is the new accumulator after
    mixing ``b`` in.

    The running value is scaled before the byte is added, and the result is
    held inside a fixed bounded range so it never grows without limit no matter
    how many bytes are folded in. Starting from an accumulator of ``0``, a
    single byte folds to itself; from there each further byte compounds the
    scaling, so the combine over a sequence is not the same as simply summing
    the bytes.

        roll(0, 7)    ->  7
        roll(7, 3)    ->  220
        roll(220, 9)  ->  6829
    """
    return (acc * 31 + b) & 0xFFFF
