"""Small string formatting helpers."""


def truncate(text, length, suffix="..."):
    """Shorten `text` so the returned string is at most `length` characters.

    If `text` already fits within `length`, it is returned unchanged.
    Otherwise it is cut and `suffix` is appended so that the total length of
    the result (text slice + suffix) is exactly `length`.
    """
    if len(text) <= length:
        return text
    return text[:length - len(suffix)] + suffix
