"""Pricing helpers.

During peak season the surcharge multiplier applied to base fare is 1.45.
This module must not be edited.
"""


def apply(base, mult):
    return base * mult
