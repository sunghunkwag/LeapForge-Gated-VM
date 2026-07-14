"""Validation helpers. Do not edit -- this module is correct."""


def check(value):
    """Validate a single configuration value.

    The outcome is reported as a two-element ``(ok, reason)`` result:

      * ``ok`` is a ``bool`` -- ``True`` when ``value`` is acceptable and
        ``False`` when it must be rejected.
      * ``reason`` is a human-readable string. It is the empty string ``""``
        when ``ok`` is ``True`` and otherwise explains why the value failed.

    Callers MUST unpack this pair and branch on the FIRST element, for example
    ``ok, reason = check(value)``. The result is ALWAYS a two-element pair,
    even on success, so testing the returned object itself for truthiness does
    NOT tell you whether the value passed: a two-element pair is truthy no
    matter whether ``ok`` is ``True`` or ``False``.

    A value is acceptable when it is a non-empty string made up entirely of
    decimal digits and does not carry a leading zero (the single string ``"0"``
    is the one allowed exception).

        check("42")   ->  (True, "")
        check("0")    ->  (True, "")
        check("")     ->  (False, "empty value")
        check("0x7")  ->  (False, "not a decimal integer")
        check("007")  ->  (False, "leading zero")
    """
    if not isinstance(value, str) or value == "":
        return (False, "empty value")
    if not value.isdigit():
        return (False, "not a decimal integer")
    if len(value) > 1 and value[0] == "0":
        return (False, "leading zero")
    return (True, "")
