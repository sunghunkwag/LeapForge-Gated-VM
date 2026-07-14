from main import auth_word

def test_public():
    assert isinstance(auth_word(), str)
