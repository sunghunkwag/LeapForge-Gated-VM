from helpers import roll
from main import rebuild


def _reference(data):
    """The true whole-sequence combine, built straight from the correct,
    non-editable one-step helper."""
    acc = 0
    for b in data:
        acc = roll(acc, b)
    return acc


def test_matches_reference_small():
    for data in ([1, 2, 3], [10, 20, 30], [5, 0, 9, 4], [3, 1, 4, 1, 5, 9]):
        assert rebuild(data) == _reference(data)


def test_matches_reference_high_bytes():
    for data in ([255, 255, 255], [200, 100, 250, 1], [128, 64, 32, 16, 8]):
        assert rebuild(data) == _reference(data)


def test_stays_within_bounded_range():
    data = list(range(1, 25)) + [255, 254, 253, 200, 199]
    result = rebuild(data)
    assert result == _reference(data)
    assert 0 <= result <= 0xFFFF


def test_two_and_more_bytes_differ_from_plain_sum():
    for data in ([42, 42], [1, 1, 1, 1], [7, 3, 9]):
        assert rebuild(data) == _reference(data)
        assert rebuild(data) != sum(data)


def test_edge_cases_still_match():
    assert rebuild([]) == _reference([]) == 0
    for data in ([0], [255], [7], [123]):
        assert rebuild(data) == _reference(data) == data[0]
