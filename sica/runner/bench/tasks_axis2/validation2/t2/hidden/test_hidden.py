from main import passing_scores


def test_score_equal_to_threshold_passes():
    assert passing_scores([60], 60) == [60]
    assert passing_scores([59, 60, 61], 60) == [60, 61]


def test_duplicates_at_threshold_all_kept():
    assert passing_scores([100, 100, 99], 100) == [100, 100]


def test_mixed_order_preserved():
    assert passing_scores([60, 70, 55, 60, 80], 60) == [60, 70, 60, 80]


def test_all_at_or_above_threshold():
    assert passing_scores([60, 61, 62], 60) == [60, 61, 62]


def test_all_below_threshold():
    assert passing_scores([1, 2, 3], 60) == []


def test_zero_threshold_includes_zero():
    assert passing_scores([0, -1, 2], 0) == [0, 2]
