"""Title casing helper."""

MINOR_WORDS = ("a", "an", "the", "of", "and", "or", "nor", "but",
               "in", "on", "at", "to", "for", "with", "by")


def title_case(text, minor_words=MINOR_WORDS):
    """Capitalize a phrase as a title.

    Every word is capitalized except the "minor" words (articles, short
    conjunctions and prepositions), which are kept lowercase. As an
    exception, the first and last words of the title are ALWAYS capitalized,
    even when they are minor words.
    """
    words = text.split()
    last = len(words) - 1
    result = []
    for i, word in enumerate(words):
        lowered = word.lower()
        if i != 0 and lowered in minor_words:
            result.append(lowered)
        else:
            result.append(lowered.capitalize())
    return " ".join(result)
