"""Public regression guard: behaviour that must keep working.

These cases already pass on the shipped code; they protect against a fix that
breaks the clearly-shorter and clearly-longer paths.
"""
from core import truncate


def test_short_text_unchanged():
    assert truncate("hi", 10) == "hi"


def test_empty_text_unchanged():
    assert truncate("", 5) == ""


def test_long_text_is_cut_with_suffix():
    assert truncate("hello world", 8) == "hello..."


def test_custom_suffix():
    assert truncate("hello world", 6, "!") == "hello!"
