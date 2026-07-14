from core import render

def test_public():
    assert render('hello {name}', {'name':'Sam'})=='hello Sam'
    assert render('plain text', {})=='plain text'
