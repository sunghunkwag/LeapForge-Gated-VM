from core import hex_for

def test_public():
    assert hex_for('primary').startswith('#')
    assert len(hex_for('accent')) == 7
