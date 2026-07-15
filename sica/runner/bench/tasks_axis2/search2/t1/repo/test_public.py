from main import contains, index_of


def test_public():
    # Elements that ARE present resolve to their position.
    assert index_of([10, 20, 30], 20) == 1
    assert index_of(["a", "b", "c"], "a") == 0
    assert index_of([10, 20, 30], 30) == 2
    # Membership on present elements.
    assert contains([1, 2, 3], 2) is True
    assert contains(["x", "y"], "y") is True
