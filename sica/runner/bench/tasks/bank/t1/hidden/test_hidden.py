import pytest
from core import Account

def test_hidden():
    a=Account(50)
    with pytest.raises(ValueError):
        a.withdraw(100)
    assert a.balance==50
