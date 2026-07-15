from helpers import encode
from main import decode


def test_roundtrip_full_range():
    for x in range(256):
        assert decode(encode(x)) == x


def test_roundtrip_selected_cases():
    for x in (37, 40, 63, 100, 128, 200, 255):
        assert decode(encode(x)) == x
