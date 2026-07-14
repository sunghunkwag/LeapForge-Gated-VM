from core import running_total

def test_hidden():
    assert running_total([1, 2, 3]) == [1, 3, 6]
    assert running_total([5, 5]) == [5, 10]
