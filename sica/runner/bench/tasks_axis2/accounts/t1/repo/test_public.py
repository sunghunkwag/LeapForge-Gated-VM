from main import run_ledger


def test_public():
    # No transactions leaves the starting balance untouched.
    assert run_ledger([]) == 0
    assert run_ledger([], start=100) == 100
    # A deposit fully cancelled by an equal withdrawal nets back to the start.
    assert run_ledger([("deposit", 50), ("withdraw", 50)]) == 0
    assert run_ledger([("deposit", 200), ("withdraw", 200)], start=100) == 100
    # The final balance comes back as an integer number of cents.
    assert isinstance(run_ledger([("deposit", 10)]), int)
