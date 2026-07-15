from main import can_withdraw


def test_public():
    # Withdrawing strictly less than the balance is always fine.
    assert can_withdraw(100, 40) is True
    assert can_withdraw(100, 99) is True
    # Withdrawing strictly more than the balance is never allowed.
    assert can_withdraw(100, 150) is False
    assert can_withdraw(0, 1) is False
