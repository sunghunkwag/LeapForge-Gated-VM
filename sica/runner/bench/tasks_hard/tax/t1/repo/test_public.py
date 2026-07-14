from core import taxed

def test_public():
    assert taxed(100, 'food') >= 100
