from core import Account, transfer

def test_public():
    a=Account(100); b=Account(0)
    transfer(a,b,40)
    assert b.balance==40
