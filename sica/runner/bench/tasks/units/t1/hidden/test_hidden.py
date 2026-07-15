from core import c_to_f

def test_hidden():
    assert c_to_f(0)==32
    assert c_to_f(100)==212
    assert c_to_f(37)==98.6
