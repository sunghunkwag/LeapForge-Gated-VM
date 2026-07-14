from main import window_sums


def test_public():
    # The result is always a list.
    assert isinstance(window_sums([1, 2, 3, 4], 2), list)
    assert isinstance(window_sums([], 3), list)
    # A window longer than the data yields no windows.
    assert window_sums([1, 2], 5) == []
    assert window_sums([], 2) == []
    # Every produced window sum is an integer.
    for s in window_sums([4, 8, 15, 16, 23], 3):
        assert isinstance(s, int)
