from core import celsius_to_k

def test_hidden():
    assert celsius_to_k(0) == 273.15
    assert celsius_to_k(100) == 373.15
