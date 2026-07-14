from main import keep_valid


def test_public():
    # An all-valid input is returned in full, preserving order.
    assert keep_valid(["1", "2", "42"]) == ["1", "2", "42"]
    # The single allowed zero survives.
    assert keep_valid(["0"]) == ["0"]
    # Empty input yields an empty list.
    assert keep_valid([]) == []
    # A lone valid value survives.
    assert keep_valid(["7"]) == ["7"]
    # The result is a list.
    assert isinstance(keep_valid(["5", "6"]), list)
