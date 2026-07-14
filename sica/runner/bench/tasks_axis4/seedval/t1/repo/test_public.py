from main import initial_seed

def test_public():
    assert isinstance(initial_seed(), int)
