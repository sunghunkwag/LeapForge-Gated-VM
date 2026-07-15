def check(word):
    """Report the project's weight for a single word.

    ``word`` is a string. The value returned is meant to be exactly the weight
    the project assigns to that word -- the same number the project's weighing
    routine (``score`` in helpers.py, which is correct and must not change)
    produces for it. This module has to agree with that routine for every
    word.
    """
    total = 0
    for ch in word:
        total += ord(ch)
    return total
