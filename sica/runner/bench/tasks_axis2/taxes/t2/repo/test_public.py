from main import tax_due


def test_public():
    # At the allowance boundary exactly, nothing is taxable yet.
    assert tax_due(1000) == 0
    # Income above the allowance is taxed at 20% of the excess only.
    assert tax_due(2000) == 200
    assert tax_due(6000) == 1000
    assert tax_due(1500) == 100
