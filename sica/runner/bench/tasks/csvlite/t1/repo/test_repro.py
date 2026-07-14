"""Public reproduction of the csvlite/t1 bug (FAILS on the shipped snapshot).

A doubled quote inside a quoted field must decode to a single literal quote
character, but the shipped parser drops it entirely. This file is here to make
the failure obvious; it is not part of the regression guard.
"""

from core import parse_line


def test_doubled_quote_decodes_to_one_quote():
    # The quoted field "a""b" holds the three characters  a " b .
    assert parse_line('"a""b"') == ['a"b']
