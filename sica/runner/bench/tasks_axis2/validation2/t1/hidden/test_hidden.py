from main import keep_valid


def test_empty_strings_dropped():
    assert keep_valid(["1", "", "2"]) == ["1", "2"]
    assert keep_valid(["", ""]) == []


def test_non_digit_values_dropped():
    assert keep_valid(["9", "0x7", "3", "12a", "10"]) == ["9", "3", "10"]
    assert keep_valid(["-5", "  ", "1.0"]) == []


def test_leading_zero_dropped_but_zero_kept():
    assert keep_valid(["0", "00", "007", "10"]) == ["0", "10"]


def test_all_invalid_gives_empty():
    assert keep_valid(["", "01", "12a", "-5"]) == []


def test_all_valid_kept_in_order():
    assert keep_valid(["5", "6", "0", "100"]) == ["5", "6", "0", "100"]


def test_mixed_valid_and_invalid():
    values = ["42", "", "7", "0x1", "0", "088", "13"]
    assert keep_valid(values) == ["42", "7", "0", "13"]
