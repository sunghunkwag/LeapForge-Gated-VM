from core import round_cents

def test_hidden():
    assert round_cents(1.239) == 1.24
    assert round_cents(3.014) == 3.01
