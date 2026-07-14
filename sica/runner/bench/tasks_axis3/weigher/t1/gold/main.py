from helpers import score


def check(word):
    """Report the project's weight for a single word.

    ``word`` is a string. The value returned is exactly the weight the project
    assigns to that word -- the number produced by the project's weighing
    routine (``score`` in helpers.py, which is correct and must not change).
    That weight depends on where each letter sits in the word and carries the
    routine's fixed final adjustment, so ``check`` defers to the routine itself
    rather than recomputing a plainer, position-blind sum of the letters.
    """
    return score(word)
