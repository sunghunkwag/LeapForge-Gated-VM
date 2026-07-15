from main import contains, index_of


def test_index_of_miss_returns_default():
    # A miss must yield the requested default, never the helper's -1 sentinel.
    assert index_of([10, 20, 30], 99) is None
    assert index_of([10, 20, 30], 99, default="absent") == "absent"
    assert index_of([], 5) is None
    assert index_of([], 5, default=0) == 0
    assert index_of(["a", "b"], "z", default=-1) == -1


def test_index_of_hit_still_works():
    assert index_of([10, 20, 30], 10) == 0
    assert index_of([10, 20, 30], 30) == 2
    assert index_of(["a", "b", "c"], "c") == 2


def test_contains_miss_is_false():
    assert contains([1, 2, 3], 9) is False
    assert contains([], 1) is False
    assert contains(["x", "y"], "z") is False


def test_contains_hit_is_true():
    assert contains([1, 2, 3], 1) is True
    assert contains([1, 2, 3], 3) is True
