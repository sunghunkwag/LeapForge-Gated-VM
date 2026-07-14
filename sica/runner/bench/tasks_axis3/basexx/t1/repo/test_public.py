from main import decode, encode


def test_encode_returns_str():
    assert isinstance(encode(0), str)
    assert isinstance(encode(42), str)
    assert isinstance(encode(123), str)


def test_decode_returns_int():
    assert isinstance(decode(encode(0)), int)
    assert isinstance(decode(encode(42)), int)
    assert isinstance(decode(encode(123)), int)


def test_operations_are_deterministic():
    assert encode(50) == encode(50)
    assert decode(encode(50)) == decode(encode(50))
