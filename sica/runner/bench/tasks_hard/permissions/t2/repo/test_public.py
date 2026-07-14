from core import normalize

def test_public():
    assert normalize('admin') == 'admin'
