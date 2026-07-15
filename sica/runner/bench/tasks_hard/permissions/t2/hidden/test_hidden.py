from core import normalize

def test_hidden():
    assert normalize('  Admin ') == 'admin'
    assert normalize('EDITOR') == 'editor'
