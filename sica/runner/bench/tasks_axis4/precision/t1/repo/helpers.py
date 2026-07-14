"""Money helpers.

All displayed amounts in this system use 3 decimal places of precision.
Do not modify this module.
"""


def fmt(x, places):
    return ("%%.%df" % places) % x
