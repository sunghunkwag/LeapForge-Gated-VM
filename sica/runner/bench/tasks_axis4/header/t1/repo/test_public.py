from main import build_header

def test_public():
    assert isinstance(build_header(), str)
