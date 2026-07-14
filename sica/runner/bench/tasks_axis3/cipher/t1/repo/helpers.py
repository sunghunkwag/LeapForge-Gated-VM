"""Cipher helper. Do not edit -- this module is correct.

It defines the single per-letter transformation the cipher is built on. Any
code that needs to reverse the cipher has to reverse exactly the step defined
in the body of ``shift`` below -- there is no other description of it anywhere.
"""


def shift(code, i):
    """Encipher one letter by its position in the word.

    ``code`` is a letter's position in the lowercase alphabet (``0`` for
    ``a`` through ``25`` for ``z``). ``i`` is that letter's zero-based index
    in the word. The value returned is the enciphered position, again an
    integer in ``0..25``.

    How far a letter moves is not fixed: it depends on where the letter sits
    in the word, and the result is wrapped back around the alphabet. Two
    letters that start out the same are enciphered differently when they
    appear at different positions. Because the step is tied to the position,
    reversing the cipher means undoing the very same position-dependent step
    at each index -- moving every letter back by one flat amount does not
    recover the original word.

        shift(0, 0)  ->  5
        shift(0, 1)  ->  6
        shift(0, 2)  ->  9
    """
    return (code + (i * i + 5)) % 26
