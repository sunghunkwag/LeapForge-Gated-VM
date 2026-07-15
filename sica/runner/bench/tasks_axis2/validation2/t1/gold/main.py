from helpers import check


def keep_valid(values):
    """Filter a list of configuration values, keeping only the valid ones.

    ``values`` is a list of strings. Each is validated with the ``check``
    helper imported from ``helpers``. Returns a new list containing, in their
    original order, exactly those values that pass validation.
    """
    kept = []
    for value in values:
        ok, _reason = check(value)
        if ok:
            kept.append(value)
    return kept
