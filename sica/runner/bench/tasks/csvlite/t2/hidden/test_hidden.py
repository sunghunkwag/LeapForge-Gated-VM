"""Hidden grading tests for csvlite/t2.

A double quote opens a quoted field only when it is the first character of the
field. A quote that appears after other characters is an ordinary literal
character. The shipped parser treats any quote as an opening quote, so a stray
mid-field quote wrongly turns on quoting and swallows the following comma(s).
These cases FAIL on the buggy snapshot and PASS once opening quotes are
restricted to the start of a field.
"""

from core import parse_line


def test_stray_quote_stays_literal_and_comma_still_splits():
    assert parse_line('ab"c,d') == ['ab"c', "d"]


def test_single_stray_quote_in_only_field():
    assert parse_line('a"b') == ['a"b']


def test_stray_quote_in_a_later_field():
    assert parse_line('x,y"z,w') == ["x", 'y"z', "w"]


def test_stray_quote_between_digits():
    assert parse_line('12"34') == ['12"34']


def test_stray_quote_and_real_quoted_field_together():
    assert parse_line('a"b,"c,d"') == ['a"b', "c,d"]


def test_well_formed_records_still_parse():
    # Behaviour unchanged by the fix must keep working.
    assert parse_line('"a,b",c') == ["a,b", "c"]
    assert parse_line('"x""y"') == ['x"y']
    assert parse_line("a,b,c") == ["a", "b", "c"]
