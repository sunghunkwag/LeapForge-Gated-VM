from main import decode


def test_decode_returns_int():
    assert isinstance(decode(0), int)
    assert isinstance(decode(128), int)
    assert isinstance(decode(255), int)
