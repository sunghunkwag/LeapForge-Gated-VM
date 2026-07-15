def parse_setting(s):
    """Parse a ``"key:value"`` setting string into a ``(key, value)`` tuple.

    ``s`` contains at least one ``":"``. The key is everything before the
    FIRST colon; the value is everything after it. Only that first colon acts
    as the separator -- any further colons belong to the value and must be
    kept, so ``"host:localhost:8080"`` parses to ``("host", "localhost:8080")``
    and ``"k:"`` (nothing after the colon) parses to ``("k", "")``.
    """
    parts = s.split(":")
    return parts[0], parts[1]
