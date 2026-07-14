from main import auth_word

def test_hidden():
    assert auth_word() == "MARIGOLD"
