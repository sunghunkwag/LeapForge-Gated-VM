from helpers import fwd
from main import back


def test_roundtrip_low_positions():
    for x in range(0, 12):
        assert back(fwd(x)) == x


def test_roundtrip_selected_positions():
    for x in (13, 19, 24, 30, 37, 42, 48, 49):
        assert back(fwd(x)) == x


def test_roundtrip_full_domain():
    for x in range(50):
        assert back(fwd(x)) == x
