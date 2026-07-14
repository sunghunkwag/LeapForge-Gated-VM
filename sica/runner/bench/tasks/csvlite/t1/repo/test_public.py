"""Public regression guard for csvlite/t1 (passes on the shipped snapshot).

None of these records use the doubled-quote ("") escape, so the reported bug
does not touch them: plain fields, quoted fields containing commas, and empty
fields all parse the same on the shipped code. They guard the basic parsing
paths against a fix that breaks them.
"""

from core import parse_line


def test_plain_fields():
    assert parse_line("a,b,c") == ["a", "b", "c"]


def test_single_field():
    assert parse_line("hello") == ["hello"]


def test_empty_string_is_one_empty_field():
    assert parse_line("") == [""]


def test_empty_fields_between_commas():
    assert parse_line("a,,c") == ["a", "", "c"]


def test_trailing_comma_yields_empty_field():
    assert parse_line("a,b,") == ["a", "b", ""]


def test_quoted_field_keeps_inner_comma():
    assert parse_line('"a,b",c') == ["a,b", "c"]


def test_all_fields_quoted():
    assert parse_line('"hello","world"') == ["hello", "world"]
