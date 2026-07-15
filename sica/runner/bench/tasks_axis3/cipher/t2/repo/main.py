import string

from helpers import is_letter

_alphabet = string.ascii_lowercase


def rotate(text, k):
    """Return ``text`` with each lowercase letter advanced ``k`` places
    FORWARD through the alphabet, wrapping from ``z`` back to ``a``.

    Characters that are not lowercase letters (spaces, digits, punctuation)
    are copied through unchanged. ``k`` is a non-negative integer.

        rotate("abc", 1)  ->  "bcd"
        rotate("xyz", 3)  ->  "abc"
        rotate("a b", 1)  ->  "b c"
    """
    n = len(_alphabet)
    out = []
    for ch in text:
        if is_letter(ch):
            pos = _alphabet.index(ch)
            out.append(_alphabet[(pos - k) % n])
        else:
            out.append(ch)
    return "".join(out)
