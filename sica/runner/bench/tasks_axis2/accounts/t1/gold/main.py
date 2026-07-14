from helpers import apply


def run_ledger(transactions, start=0):
    """Apply a sequence of transactions to a starting balance.

    ``transactions`` is a list of ``(kind, amount)`` pairs. Returns the final
    balance (an integer number of cents) after applying every transaction in
    order, beginning from ``start``.
    """
    balance = start
    for tx in transactions:
        balance = apply(balance, tx)
    return balance
