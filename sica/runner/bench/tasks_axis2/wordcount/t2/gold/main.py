def count_long_words(text, min_len):
    """Count the words in ``text`` that are at least ``min_len`` characters.

    ``text`` is split on whitespace into words. The result is the number of
    those words whose length is greater than or equal to ``min_len`` -- a word
    exactly ``min_len`` characters long counts. ``min_len`` is a positive
    integer.
    """
    return sum(1 for w in text.split() if len(w) >= min_len)
