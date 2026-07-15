from helpers import pack


def unpack(raw):
    """Recover the original value from its packed, fixed-point form.

    ``unpack`` is meant to be the exact inverse of the scaler's ``pack``
    routine, so that ``unpack(pack(v)) == v`` for every value ``v``. It
    currently undoes the scaling but does not fully reverse everything
    ``pack`` did, so the round-trip does not return the original value.
    """
    step = pack(1) - pack(0)
    return raw / step
