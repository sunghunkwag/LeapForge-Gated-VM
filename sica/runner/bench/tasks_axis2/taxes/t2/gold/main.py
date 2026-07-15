def tax_due(income):
    """Return the tax due on ``income`` (a non-negative integer of cents).

    The first 1000 cents of income are covered by a standard allowance and
    are tax-free. Only the portion of income ABOVE 1000 cents is taxed, at a
    flat rate of 20%. Incomes at or below the 1000-cent allowance owe no tax
    at all, so the tax due is never negative.
    """
    taxable = max(income - 1000, 0)
    return taxable * 20 // 100
