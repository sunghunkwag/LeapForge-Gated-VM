from core import grade

def test_public():
    assert grade(100) == 'A'
    assert grade(0) == 'F'
