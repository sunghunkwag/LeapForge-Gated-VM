from helpers import pack
from main import unpack


def test_roundtrip_small_values():
    for v in (0, 1, 2, 3, 5, 8):
        assert unpack(pack(v)) == v


def test_roundtrip_larger_values():
    for v in (25, 42, 99, 250, 1234):
        assert unpack(pack(v)) == v


def test_roundtrip_negative_values():
    for v in (-1, -4, -37, -250):
        assert unpack(pack(v)) == v
