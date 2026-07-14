from main import rotate


def test_public():
    # A zero rotation returns the text unchanged.
    assert rotate("hello", 0) == "hello"
    assert rotate("abc xyz", 0) == "abc xyz"
    # Characters that are not lowercase letters are copied through unchanged.
    assert rotate("!?. ", 4) == "!?. "
    assert rotate("12 34", 7) == "12 34"
    # A full turn of the alphabet lands back on the same letters.
    assert rotate("cipher", 26) == "cipher"
    # The result is a string of the same length as the input.
    result = rotate("secret code", 5)
    assert isinstance(result, str)
    assert len(result) == len("secret code")
