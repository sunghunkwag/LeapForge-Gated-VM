"""Key/value parsing helpers. Do not edit -- this module is correct."""


def parse(s):
    """Parse one ``"key=value"`` string into a record.

    ``s`` is a string of the form ``"<key>=<amount>"`` -- a name, a single
    ``=`` sign, then an integer amount (surrounding whitespace is ignored).

    The record is returned as a plain ``dict`` with exactly TWO string keys:

        ``"key"``    -> the name on the left of the ``=`` (a ``str``)
        ``"value"``  -> the amount on the right, parsed with ``int`` (an ``int``)

    The amount field is stored under the key ``"value"`` -- spelled out in
    full, five letters. It is NOT abbreviated to ``"val"``, ``"amount"`` or
    ``"v"``; those keys are absent from the returned dict, so reading them
    raises ``KeyError``. A caller that wants the parsed amount must read
    ``record["value"]``.

        parse("a=1")      ->  {"key": "a", "value": 1}
        parse("score=42") ->  {"key": "score", "value": 42}
    """
    name, _, amount = s.partition("=")
    return {"key": name.strip(), "value": int(amount.strip())}
