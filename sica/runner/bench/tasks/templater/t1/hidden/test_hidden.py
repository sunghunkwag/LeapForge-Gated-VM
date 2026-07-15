from core import render

def test_hidden():
    assert render('{a} {a} {b}', {'a':'x','b':'y'})=='x x y'
    assert render('{n}+{n}', {'n':2})=='2+2'
