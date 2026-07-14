from core import taxed

def test_hidden():
    assert taxed(100, 'food') == 102.0
    assert taxed(200, 'book') == 211.0
    assert taxed(50, 'luxury') == 61.25
