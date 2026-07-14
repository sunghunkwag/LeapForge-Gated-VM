from main import round_amount

def test_hidden():
    assert round_amount(1.23456) == 1.235
    assert round_amount(2.0001) == 2.0
