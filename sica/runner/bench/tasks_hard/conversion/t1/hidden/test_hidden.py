from core import to_metres

def test_hidden():
    assert to_metres(1, 'mi') == 1609.34
    assert to_metres(10, 'ft') == 3.048
    assert to_metres(2, 'yd') == 1.8288
