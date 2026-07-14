from core import fee

def test_hidden():
    assert fee('wire', 500) == 25.0
    assert fee('ach', 500) == 1.5
    assert fee('card', 100) == 2.9
