"""Basexx helper. Do not edit -- this module is correct.

It defines the single encoding step the codec is built on: how a non-negative
integer is turned into its stored code string. Any code that needs to recover
the original number has to undo exactly the step written in the body of
``enc`` below -- there is no other description of it anywhere.
"""


def enc(n):
    """Turn a non-negative integer into its stored code string.

    The number is written out one digit at a time in a small fixed radix, and
    each digit is emitted not as itself but as the letter that sits at that
    position in a fixed run of capital letters. The digits are laid down most
    significant first, so a short number gives a short string. Zero is the
    single lowest letter.

        enc(0)   ->  "G"
        enc(1)   ->  "T"
        enc(6)   ->  "K"
        enc(7)   ->  "TG"
        enc(10)  ->  "TW"

    Two different numbers never encode to the same string, so a correct
    inverse recovers each original exactly.
    """
    alphabet = "GTPWABK"
    if n == 0:
        return alphabet[0]
    out = []
    while n > 0:
        out.append(alphabet[n % 7])
        n //= 7
    out.reverse()
    return "".join(out)
