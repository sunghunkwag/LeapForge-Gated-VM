from main import decode, encode


def test_round_trip_short_words():
    for word in ("a", "hi", "cat", "code"):
        assert decode(encode(word)) == word


def test_round_trip_longer_words():
    for word in ("cipher", "hello", "abcdef", "position"):
        assert decode(encode(word)) == word


def test_round_trip_full_alphabet():
    word = "abcdefghijklmnopqrstuvwxyz"
    assert decode(encode(word)) == word


def test_first_letter_is_restored():
    # Enciphering moves even the very first letter, so the round-trip has to
    # move it back rather than leave it in place.
    assert decode(encode("z")) == "z"
    assert decode(encode("m")) == "m"
    assert decode(encode("a")) == "a"


def test_round_trip_repeated_letters():
    for word in ("banana", "mississippi", "zzz", "abcabcabc"):
        assert decode(encode(word)) == word
