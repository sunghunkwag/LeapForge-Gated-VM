from core import render

def test_hidden():
    assert render('{{name}}', {'name':'Sam'})=='{name}'
    assert render('{{x}} {y}', {'y':'Z'})=='{x} Z'
