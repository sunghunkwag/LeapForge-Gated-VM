"""Public reproduction of the bug (FAILS on the buggy snapshot).

This is intentionally *not* part of pass_to_pass -- it demonstrates the
reported failure so the fix target is obvious.
"""

from core import chunk


def test_chunk_keeps_final_partial_chunk():
    # Five items in chunks of two: the trailing [5] must be preserved.
    assert chunk([1, 2, 3, 4, 5], 2) == [[1, 2], [3, 4], [5]]
