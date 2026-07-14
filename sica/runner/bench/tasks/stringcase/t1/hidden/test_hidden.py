"""Hidden grading tests for truncate (the fail->pass signal)."""
from core import truncate


def test_exact_length_boundary():
    # len(text) == length must be returned unchanged (the reported bug).
    assert truncate("hello", 5) == "hello"
    assert truncate("abc", 3) == "abc"
    assert truncate("abcdef", 6) == "abcdef"


def test_one_over_length_is_truncated():
    # len(text) == length + 1 must be truncated to exactly `length`.
    assert truncate("abcdef", 5) == "ab..."
    assert truncate("hello!", 5) == "he..."


def test_clearly_longer_is_truncated():
    result = truncate("abcdefghij", 7)
    assert result == "abcd..."
    assert len(result) == 7


def test_clearly_shorter_unchanged():
    assert truncate("hi", 10) == "hi"
    assert truncate("x", 3) == "x"


def test_custom_suffix_boundary():
    assert truncate("hello", 5, "!") == "hello"
    assert truncate("hello!", 5, "!") == "hell!"
