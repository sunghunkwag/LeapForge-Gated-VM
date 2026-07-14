"""Character helpers. Do not edit -- this module is correct."""


def is_letter(ch):
    """Return True if ``ch`` is a single lowercase ASCII letter (``a``-``z``)."""
    return len(ch) == 1 and "a" <= ch <= "z"
