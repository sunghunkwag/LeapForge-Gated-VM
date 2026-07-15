"""Ledger helpers. Do not edit -- this module is correct."""


def apply(balance, tx):
    """Compute the balance that results from applying one transaction.

    ``balance`` is an integer number of cents. ``tx`` is a ``(kind, amount)``
    pair where ``kind`` is ``"deposit"`` or ``"withdraw"`` and ``amount`` is a
    non-negative integer number of cents.

    This function is pure: it changes nothing in place. ``balance`` arrives as
    a plain ``int``, and ints are immutable, so there is nothing here that can
    be altered under the caller's feet. Rather than write anything back, it
    works out the new balance and hands it over as the value it gives back to
    the caller. The caller has to keep that value and feed it into the next
    call, threading it along like ``balance = apply(balance, tx)``. If the
    caller instead invokes ``apply(balance, tx)`` on its own and lets the
    resulting value fall on the floor, its running balance stays exactly where
    it was, since nothing was ever stored back into ``balance``.

        apply(100, ("deposit", 50))   ->  150
        apply(100, ("withdraw", 30))  ->  70
    """
    kind, amount = tx
    if kind == "deposit":
        return balance + amount
    if kind == "withdraw":
        return balance - amount
    raise ValueError("unknown transaction kind: %r" % (kind,))
