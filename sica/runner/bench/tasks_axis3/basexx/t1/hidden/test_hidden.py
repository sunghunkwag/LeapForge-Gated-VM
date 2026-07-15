from main import decode, encode


def test_round_trip_single_letter_codes():
    # Numbers small enough that the code is a single letter; every one of
    # them has to come back unchanged.
    for n in (0, 1, 2, 3, 4, 5, 6):
        assert decode(encode(n)) == n


def test_round_trip_multi_letter_codes():
    for n in (7, 8, 10, 20, 48, 49, 100, 342, 1000):
        assert decode(encode(n)) == n


def test_round_trip_full_range():
    for n in range(400):
        assert decode(encode(n)) == n


def test_specific_cases():
    assert decode(encode(4)) == 4
    assert decode(encode(5)) == 5
    assert decode(encode(6)) == 6
    assert decode(encode(10)) == 10
