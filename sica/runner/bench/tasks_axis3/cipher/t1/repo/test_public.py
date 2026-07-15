from main import decode, encode


def test_public():
    # Enciphering or deciphering an empty string gives an empty string.
    assert encode("") == ""
    assert decode("") == ""
    # Both operations return strings.
    assert isinstance(encode("cipher"), str)
    assert isinstance(decode("cipher"), str)
    # The output has the same length as the input.
    assert len(encode("hello")) == len("hello")
    assert len(decode("world")) == len("world")
    # Every output character stays within the lowercase alphabet.
    for ch in encode("thequickbrownfox"):
        assert "a" <= ch <= "z"
    for ch in decode("thequickbrownfox"):
        assert "a" <= ch <= "z"
