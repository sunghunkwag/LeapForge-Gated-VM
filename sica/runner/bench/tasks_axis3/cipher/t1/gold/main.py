import string

from helpers import shift

_alphabet = string.ascii_lowercase


def _to_code(ch):
    """Position of a lowercase letter in the alphabet (``a`` -> 0)."""
    return _alphabet.index(ch)


def _to_char(code):
    """Letter at a given alphabet position, wrapping around the alphabet."""
    return _alphabet[code % len(_alphabet)]


def encode(text):
    """Encipher ``text`` (a string of lowercase letters).

    Each letter is transformed according to its position in the string using
    the project's per-letter step, and the enciphered letters are joined back
    into a string of the same length. An empty string enciphers to an empty
    string.
    """
    out = []
    for i, ch in enumerate(text):
        out.append(_to_char(shift(_to_code(ch), i)))
    return "".join(out)


def unshift(code, i):
    """Undo the enciphering step for the letter at index ``i``.

    ``code`` is an enciphered alphabet position (``0..25``) and ``i`` is the
    letter's zero-based index in the word. This must return the original
    position, i.e. it must reverse exactly what the encipher step did at this
    index, so that :func:`decode` is the inverse of :func:`encode`.
    """
    return (code - (i * i + 5)) % len(_alphabet)


def decode(text):
    """Recover the original text from :func:`encode`.

    Walks the enciphered string left to right and reverses the per-position
    step for each letter, returning a string of the same length. ``decode``
    is meant to satisfy ``decode(encode(word)) == word`` for any lowercase
    word.
    """
    out = []
    for i, ch in enumerate(text):
        out.append(_to_char(unshift(_to_code(ch), i)))
    return "".join(out)
