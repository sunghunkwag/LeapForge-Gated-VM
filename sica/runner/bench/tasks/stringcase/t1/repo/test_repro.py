"""Public reproduction of the reported bug.

This FAILS on the shipped code and should PASS once the boundary is fixed:
a string whose length equals `length` must be returned unchanged, not
truncated.
"""
from core import truncate


def test_exact_length_is_not_truncated():
    assert truncate("hello", 5) == "hello"
