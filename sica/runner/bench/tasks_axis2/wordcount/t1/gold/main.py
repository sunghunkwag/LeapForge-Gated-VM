def preview(text, max_chars):
    """Return a short preview of ``text`` capped at ``max_chars`` characters.

    ``text`` is an arbitrary string and ``max_chars`` is a non-negative
    integer. The preview is the leading portion of ``text`` that is no longer
    than ``max_chars`` characters; if ``text`` is already at most
    ``max_chars`` characters long the whole string is returned unchanged.
    """
    return text[:max_chars]
