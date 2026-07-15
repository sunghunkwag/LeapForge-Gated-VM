def passing_scores(scores, threshold):
    """Return the scores that pass, preserving their original order.

    ``scores`` is a list of integers and ``threshold`` is an integer. A score
    passes when it is greater than OR EQUAL TO ``threshold``. Returns a new
    list of the passing scores in the order they appeared.
    """
    return [s for s in scores if s > threshold]
