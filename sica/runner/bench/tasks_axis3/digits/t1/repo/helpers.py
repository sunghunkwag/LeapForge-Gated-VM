"""Digits helper. Do not edit -- this module is correct.

It defines the single mixing step the codec is built on: how a number is
scrambled into its stored code. Any code that needs to recover the original
number has to undo exactly the step written in the body of ``mix`` below --
there is no other description of it anywhere.
"""


def mix(n):
    """Scramble a number into its stored code.

    The number is spread out by a small whole-number factor, a fixed offset
    is added, and the result is kept inside a fixed range by wrapping it back
    around whenever it grows past the top of that range. Because of the wrap,
    the stored code is not simply the spread-out number: recovering the
    original has to undo the wrap as well as the offset and the spreading.

        mix(0)    ->  2
        mix(1)    ->  5
        mix(10)   ->  32
        mix(333)  ->  1     (wrapped back around the range)
        mix(500)  ->  502
        mix(999)  ->  999

    Two different numbers in range never mix to the same code, so a correct
    inverse recovers each original exactly.
    """
    return (n * 3 + 2) % 1000
