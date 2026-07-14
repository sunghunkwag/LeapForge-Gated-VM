"""Weigher helper. Do not edit -- this module is correct.

It defines the single weighing rule the whole project is built on: how much a
word weighs. Any code that needs the weight of a word has to reproduce exactly
the rule written in the body of ``score`` below -- there is no other
description of it anywhere.
"""


def score(word):
    """Return the project's weight for ``word``.

    ``word`` is a string. Each letter contributes to the total according to
    *where it sits* in the word: a letter counts for more the further along it
    is, so the same letters arranged in a different order weigh differently.
    On top of the per-letter contributions the weight carries a fixed final
    adjustment that every word receives, so even the empty word has a weight.

        score("")    ->  13
        score("a")   ->  110
        score("ab")  ->  306
        score("ba")  ->  305

    Because a letter's contribution depends on its position, no plain,
    position-blind sum of the letters reproduces this weight, and because of
    the fixed final adjustment the weight is never just the sum of the
    per-letter contributions either.
    """
    total = 0
    for index, ch in enumerate(word):
        total += (index + 1) * ord(ch)
    return total + 13
