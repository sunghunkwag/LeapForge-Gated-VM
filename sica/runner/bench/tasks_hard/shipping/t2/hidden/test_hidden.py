from core import combine

def test_hidden():
    x = [1, 2]
    combine(x, [3])
    assert x == [1, 2]
