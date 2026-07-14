"""Rolling checksum over a sequence of bytes.

The project's one-step rolling combine lives in ``roll`` in ``helpers.py``
(correct, do not edit). ``rebuild`` recomputes the whole-sequence combine and
is meant to agree with folding that single step across every byte.
"""


def rebuild(data):
    """Recompute the project's rolling combine over ``data``.

    ``data`` is a list of byte values, each an integer in ``0..255``. The
    return value is the single integer you get by feeding the bytes one at a
    time through the project's one-step rolling combine, starting from an
    accumulator of ``0``. An empty list combines to ``0`` and a single byte
    combines to itself.
    """
    acc = 0
    for b in data:
        acc = acc * 17 + b
    return acc
