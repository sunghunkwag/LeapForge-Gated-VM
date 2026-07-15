def can_withdraw(balance, amount):
    """Return True if ``amount`` can be withdrawn from ``balance``.

    A withdrawal is allowed as long as it does not exceed the available
    balance. Withdrawing the entire balance (``amount == balance``) is allowed
    and leaves a balance of zero. ``amount`` and ``balance`` are non-negative
    integers.
    """
    return amount <= balance
