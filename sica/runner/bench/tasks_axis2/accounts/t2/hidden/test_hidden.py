from main import can_withdraw


def test_exact_balance_is_withdrawable():
    assert can_withdraw(100, 100) is True
    assert can_withdraw(50, 50) is True
    assert can_withdraw(1, 1) is True


def test_zero_amount_always_ok():
    assert can_withdraw(0, 0) is True
    assert can_withdraw(100, 0) is True


def test_below_balance_ok():
    assert can_withdraw(100, 30) is True
    assert can_withdraw(10, 9) is True


def test_above_balance_rejected():
    assert can_withdraw(100, 101) is False
    assert can_withdraw(0, 5) is False
    assert can_withdraw(50, 51) is False
