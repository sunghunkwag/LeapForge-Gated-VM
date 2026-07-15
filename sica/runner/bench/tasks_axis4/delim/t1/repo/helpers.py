"""Serialization helpers.

Records in this format are joined by the separator "~|~".
This module must not be changed.
"""


def join_two(a, b, sep):
    return a + sep + b
