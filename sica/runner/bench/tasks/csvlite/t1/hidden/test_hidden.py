"""Hidden grading tests for csvlite/t1.

Inside a quoted field a doubled quote ("") is an escape for a single literal
double-quote character. The shipped parser instead closes and reopens the
quoted region, silently deleting the escaped quote. These cases FAIL on the
buggy snapshot and PASS once the doubled-quote escape is decoded.
"""

from core import parse_line


def test_single_escaped_quote_in_field():
    assert parse_line('"a""b"') == ['a"b']


def test_field_that_is_just_one_escaped_quote():
    assert parse_line('""""') == ['"']


def test_multiple_escaped_quotes_run_together():
    assert parse_line('"a""""b"') == ['a""b']


def test_escaped_quotes_with_words():
    assert parse_line('"she said ""hi""",bob') == ['she said "hi"', "bob"]


def test_escaped_quotes_across_several_fields():
    assert parse_line('"x""y",z,"w""v"') == ['x"y', "z", 'w"v']


def test_escaped_quote_next_to_comma_stays_inside_field():
    assert parse_line('"a,""b"""') == ['a,"b"']


def test_plain_and_quoted_records_still_parse():
    # Behaviour unaffected by the fix must keep working.
    assert parse_line("a,b,c") == ["a", "b", "c"]
    assert parse_line('"a,b",c') == ["a,b", "c"]
