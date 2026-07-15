from main import max_attempts

def test_public():
    assert isinstance(max_attempts(), int)
