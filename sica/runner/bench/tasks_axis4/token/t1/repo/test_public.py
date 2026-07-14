from main import api_prefix

def test_public():
    assert api_prefix().startswith("/")
