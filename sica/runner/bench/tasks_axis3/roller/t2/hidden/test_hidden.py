from main import window_sums


def test_basic_windows():
    assert window_sums([1, 2, 3, 4], 2) == [3, 5, 7]
    assert window_sums([1, 2, 3, 4], 1) == [1, 2, 3, 4]


def test_full_window():
    assert window_sums([1, 2, 3, 4], 4) == [10]
    assert window_sums([5, 5, 5], 3) == [15]


def test_various_lengths():
    assert window_sums([4, 8, 15, 16, 23], 3) == [27, 39, 54]
    assert window_sums([2, 4, 6, 8, 10], 2) == [6, 10, 14, 18]
    assert window_sums([10, -5, 3, 7], 2) == [5, -2, 10]


def test_edge_cases():
    assert window_sums([], 2) == []
    assert window_sums([1, 2], 5) == []
    assert window_sums([7], 1) == [7]
    assert window_sums([9], 2) == []
