from core import Account, transfer

def test_hidden():
    a=Account(100); b=Account(0)
    transfer(a,b,40)
    assert a.balance==60
    assert a.balance + b.balance == 100
