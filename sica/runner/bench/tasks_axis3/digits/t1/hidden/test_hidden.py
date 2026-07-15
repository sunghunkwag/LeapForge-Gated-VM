from main import decode, encode


def test_round_trip_small_numbers():
    for n in (0, 1, 2, 7, 10, 42, 100, 200):
        assert decode(encode(n)) == n


def test_round_trip_wrapped_numbers():
    # Numbers large enough that the mixing step wraps around its range; the
    # inverse has to undo that wrap, not just divide.
    for n in (333, 334, 500, 667, 750, 900, 999):
        assert decode(encode(n)) == n


def test_round_trip_full_range():
    for n in range(1000):
        assert decode(encode(n)) == n


def test_specific_wrapped_cases():
    assert decode(encode(500)) == 500
    assert decode(encode(700)) == 700
    assert decode(encode(999)) == 999
    assert decode(encode(333)) == 333
