from core import fee

def test_public():
    assert fee('ach', 100) < fee('wire', 100)
