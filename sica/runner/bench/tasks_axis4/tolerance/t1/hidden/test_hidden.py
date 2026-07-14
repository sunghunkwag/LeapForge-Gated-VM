from main import settings

def test_hidden():
    assert settings()["tol"] == 0.0007
