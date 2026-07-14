from main import needs_reorder, to_reorder


def test_at_threshold_triggers_reorder():
    # Stock sitting exactly at the reorder point must trigger a reorder.
    assert needs_reorder(5, 5) is True
    assert needs_reorder(0, 0) is True
    assert needs_reorder(3, 3) is True


def test_below_and_above_threshold():
    assert needs_reorder(4, 5) is True
    assert needs_reorder(1, 3) is True
    assert needs_reorder(6, 5) is False
    assert needs_reorder(10, 3) is False


def test_to_reorder_includes_items_at_threshold():
    assert to_reorder({'a': 5, 'b': 6, 'c': 3}, 5) == ['a', 'c']
    assert to_reorder({'x': 2, 'y': 2}, 2) == ['x', 'y']
    assert to_reorder({'m': 9}, 5) == []
