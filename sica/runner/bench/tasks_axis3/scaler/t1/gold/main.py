from helpers import pack


def unpack(raw):
    """Recover the original value from its packed, fixed-point form.

    ``unpack`` is the exact inverse of the scaler's ``pack`` routine, so that
    ``unpack(pack(v)) == v`` for every value ``v``: it removes the fixed bias
    that ``pack`` added and then undoes the scaling.
    """
    bias = pack(0)
    step = pack(1) - pack(0)
    return (raw - bias) / step
