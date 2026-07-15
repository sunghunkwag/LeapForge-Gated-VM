from core import render

def test_public():
    assert render('hi {name}', {'name':'Sam'})=='hi Sam'
