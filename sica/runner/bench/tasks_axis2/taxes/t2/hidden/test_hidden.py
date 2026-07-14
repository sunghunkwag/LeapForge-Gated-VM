from main import tax_due


def test_below_allowance_owes_nothing():
    # Incomes under the 1000-cent allowance are fully covered and owe no tax;
    # the result must be zero, never a negative amount.
    assert tax_due(0) == 0
    assert tax_due(1) == 0
    assert tax_due(500) == 0
    assert tax_due(999) == 0


def test_never_returns_negative():
    for income in range(0, 1000, 50):
        assert tax_due(income) >= 0


def test_allowance_boundary():
    assert tax_due(1000) == 0
    # One cent over the allowance is taxable, but 20% of a single cent floors
    # to zero.
    assert tax_due(1001) == 0
    assert tax_due(1005) == 1


def test_above_allowance_taxes_excess():
    assert tax_due(1500) == 100
    assert tax_due(2000) == 200
    assert tax_due(11000) == 2000
