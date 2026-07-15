from core import round_cents

def test_public():
    assert round_cents(1.0) == 1.0
