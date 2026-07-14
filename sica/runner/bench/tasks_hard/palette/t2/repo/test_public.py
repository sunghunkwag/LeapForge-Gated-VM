from core import hex_to_rgb

def test_public():
    assert hex_to_rgb('#000000') == (0, 0, 0)
