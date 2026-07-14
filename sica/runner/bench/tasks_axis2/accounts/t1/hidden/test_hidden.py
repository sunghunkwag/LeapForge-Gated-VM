from main import run_ledger


def test_single_deposit_updates_balance():
    assert run_ledger([("deposit", 100)]) == 100
    assert run_ledger([("deposit", 100)], start=50) == 150


def test_single_withdrawal_updates_balance():
    assert run_ledger([("withdraw", 30)], start=100) == 70
    assert run_ledger([("withdraw", 100)], start=100) == 0


def test_running_balance_accumulates():
    txs = [("deposit", 100), ("deposit", 25), ("withdraw", 40)]
    assert run_ledger(txs) == 85
    assert run_ledger(txs, start=1000) == 1085


def test_order_reaches_same_net():
    a = run_ledger([("withdraw", 20), ("deposit", 70)], start=50)
    b = run_ledger([("deposit", 70), ("withdraw", 20)], start=50)
    assert a == b == 100


def test_many_transactions():
    txs = [("deposit", 10)] * 5 + [("withdraw", 3)] * 2
    assert run_ledger(txs) == 44
