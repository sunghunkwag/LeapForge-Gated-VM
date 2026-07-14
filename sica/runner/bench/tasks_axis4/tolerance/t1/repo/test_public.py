from main import settings

def test_public():
    assert settings()["mode"] == "strict"
