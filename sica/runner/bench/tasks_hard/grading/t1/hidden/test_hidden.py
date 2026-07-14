from core import grade

def test_hidden():
    assert grade(90) == 'A'
    assert grade(89) == 'B'
    assert grade(70) == 'C'
    assert grade(60) == 'D'
    assert grade(59) == 'F'
