from main import needs_reorder, to_reorder


def test_public():
    # Clearly below the threshold: reorder. Clearly above: do not.
    assert needs_reorder(2, 5) is True
    assert needs_reorder(9, 5) is False
    assert to_reorder({'a': 1, 'b': 8}, 5) == ['a']
