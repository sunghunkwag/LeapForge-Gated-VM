from core import hex_to_rgb

def test_hidden():
    assert hex_to_rgb('#112233') == (17, 34, 51)
    assert hex_to_rgb('#ff0000') == (255, 0, 0)
