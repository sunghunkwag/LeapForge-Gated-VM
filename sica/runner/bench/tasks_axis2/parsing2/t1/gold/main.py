from helpers import parse


def lookup(pairs, wanted, default=0):
    """Return the amount associated with ``wanted`` in ``pairs``.

    ``pairs`` is a list of ``"key=value"`` strings. Each string is parsed into
    a record. The first record whose key equals ``wanted`` supplies the
    result: its parsed amount is returned. If no record has a matching key
    (including when ``pairs`` is empty), ``default`` is returned instead.
    """
    for s in pairs:
        record = parse(s)
        if record["key"] == wanted:
            return record["value"]
    return default
