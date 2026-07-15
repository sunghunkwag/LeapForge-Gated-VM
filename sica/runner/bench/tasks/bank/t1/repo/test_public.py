from core import Account

def test_public():
    a=Account(100); a.deposit(50); assert a.balance==150
    a.withdraw(30); assert a.balance==120
