from calc import classify

def test_hidden():
    assert classify(3) == 9
    assert classify(5) == 25
