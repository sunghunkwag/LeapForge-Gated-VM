"""Low-level stock helpers for the inventory service. Do not edit."""


def reserve(stock, n):
    """Reserve ``n`` units against an on-hand quantity of ``stock``.

    On success this returns the number of units *left in stock* after the
    reservation -- an ``int`` that is ``>= 0`` and may legitimately be ``0``
    when a caller reserves the entire remaining stock.

    A reservation that cannot be satisfied is treated as a hard error rather
    than a silent no-op: if ``n`` exceeds ``stock`` this raises
    ``ValueError``. It never returns a boolean and never returns a negative
    number, so callers must not rely on a falsy return value to detect
    failure.
    """
    if n > stock:
        raise ValueError("cannot reserve %d units from a stock of %d"
                         % (n, stock))
    return stock - n
