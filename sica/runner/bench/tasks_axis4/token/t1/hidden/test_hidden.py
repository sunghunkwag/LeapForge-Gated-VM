from main import api_prefix

def test_hidden():
    assert api_prefix() == "/vx7/core"
