from core import penalty

def test_public():
    assert penalty(0) == 0.0
    assert penalty(100) == penalty(200)
