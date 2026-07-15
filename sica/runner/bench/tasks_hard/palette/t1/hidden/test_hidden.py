from core import hex_for

def test_hidden():
    assert hex_for('primary') == '#2a6f97'
    assert hex_for('accent') == '#e8973a'
    assert hex_for('muted') == '#8d99ae'
