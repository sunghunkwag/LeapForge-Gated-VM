"""Public regression guard for listalgo (passes on the buggy snapshot)."""

import pytest

from core import chunk, dedup, running_max


def test_chunk_even_division():
    assert chunk([1, 2, 3, 4], 2) == [[1, 2], [3, 4]]
    assert chunk([1, 2, 3, 4, 5, 6], 3) == [[1, 2, 3], [4, 5, 6]]


def test_chunk_exact_single_chunk():
    assert chunk([1, 2, 3], 3) == [[1, 2, 3]]


def test_chunk_empty():
    assert chunk([], 4) == []


def test_chunk_invalid_size():
    with pytest.raises(ValueError):
        chunk([1, 2, 3], 0)
    with pytest.raises(ValueError):
        chunk([1, 2, 3], -1)


def test_dedup_and_running_max_unaffected():
    assert dedup([1, 1, 2, 3, 2]) == [1, 2, 3]
    assert running_max([1, 3, 2, 5]) == [1, 3, 3, 5]
