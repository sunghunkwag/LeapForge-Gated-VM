"""Public regression guard for csvlite/t2 (passes on the shipped snapshot).

Every record here is well formed: any double quote that appears sits at the
start of its field, so the shipped parser and a corrected parser agree on all
of them. They guard the field-splitting, quoted-comma, and doubled-quote paths
against a fix that breaks them.
"""

from core import parse_line


def test_plain_fields():
    assert parse_line("a,b,c") == ["a", "b", "c"]


def test_single_field():
    assert parse_line("x") == ["x"]


def test_empty_fields_between_commas():
    assert parse_line("a,,c") == ["a", "", "c"]


def test_quoted_field_keeps_inner_comma():
    assert parse_line('"a,b",c') == ["a,b", "c"]


def test_all_fields_quoted():
    assert parse_line('"a","b"') == ["a", "b"]


def test_doubled_quote_inside_quoted_field():
    assert parse_line('"x""y"') == ['x"y']


def test_quoted_field_with_only_commas():
    assert parse_line('"quoted, with, commas"') == ["quoted, with, commas"]
