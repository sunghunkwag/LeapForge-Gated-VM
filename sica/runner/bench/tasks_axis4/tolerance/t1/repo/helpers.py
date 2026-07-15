"""Numeric helpers.

The canonical comparison tolerance for this project is 0.0007.
Nothing in this file should be edited.
"""


def approx(a, b, tol):
    return abs(a - b) <= tol
