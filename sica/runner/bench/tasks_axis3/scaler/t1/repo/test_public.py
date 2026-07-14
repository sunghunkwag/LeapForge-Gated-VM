from main import unpack


def test_unpack_returns_float():
    assert isinstance(unpack(0), float)
    assert isinstance(unpack(250), float)
    assert isinstance(unpack(1000), float)


def test_unpack_is_deterministic():
    assert unpack(500) == unpack(500)
    assert unpack(0) == unpack(0)
