"""Hidden grading tests for listalgo/t1 (chunk keeps every element)."""

from core import chunk


def test_partial_last_chunk_size_two():
    assert chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]


def test_partial_last_chunk_size_three():
    assert chunk([1, 2, 3, 4, 5, 6, 7], 3) == [[1, 2, 3], [4, 5, 6], [7]]


def test_size_larger_than_list():
    assert chunk([1, 2], 5) == [[1, 2]]


def test_single_element_from_bigger_size():
    assert chunk([42], 3) == [[42]]


def test_size_one_yields_singletons():
    assert chunk([9, 8, 7], 1) == [[9], [8], [7]]


def test_no_items_are_dropped():
    data = list(range(10))
    flat = [x for c in chunk(data, 3) for x in c]
    assert flat == data
    # last chunk holds the remainder
    assert chunk(data, 3)[-1] == [9]


def test_still_handles_even_division():
    assert chunk([1, 2, 3, 4], 2) == [[1, 2], [3, 4]]
