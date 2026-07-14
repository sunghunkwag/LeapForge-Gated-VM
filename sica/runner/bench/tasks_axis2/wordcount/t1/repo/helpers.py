"""Text helpers. Do not edit -- this module is correct."""


def truncate(s, n):
    """Return the leading portion of ``s`` shortened to ``n``.

    ``s`` is arbitrary text. The shortening is done by WORDS, not by
    characters: ``s`` is split on whitespace, the first ``n`` whitespace-
    separated words are kept, and those words are rejoined with single spaces.
    The value of ``n`` is therefore a count of words -- ``n == 3`` keeps three
    whole words no matter how many characters they span, and a single word is
    never cut in the middle. It is never interpreted as a character budget: a
    long word is returned whole even when it is far longer than ``n``
    characters, and short words are packed in until ``n`` of them have been
    taken.

    If ``s`` holds ``n`` words or fewer the whole (whitespace-normalised) text
    comes back. If ``n`` is zero the empty string comes back.

        truncate("the quick brown fox", 2)  ->  "the quick"
        truncate("hello", 5)                ->  "hello"
        truncate("supercalifragilistic", 3) ->  "supercalifragilistic"
    """
    words = s.split()
    return " ".join(words[:n])
