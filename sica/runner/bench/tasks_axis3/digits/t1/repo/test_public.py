from main import decode, encode


def test_encode_returns_int():
    assert isinstance(encode(0), int)
    assert isinstance(encode(42), int)
    assert isinstance(encode(750), int)


def test_decode_returns_int():
    assert isinstance(decode(0), int)
    assert isinstance(decode(42), int)
    assert isinstance(decode(750), int)


def test_operations_are_deterministic():
    assert encode(123) == encode(123)
    assert decode(123) == decode(123)
    assert encode(0) == encode(0)
