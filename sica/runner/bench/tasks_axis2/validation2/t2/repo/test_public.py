from main import passing_scores


def test_public():
    # Scores strictly above the threshold are kept, in order.
    assert passing_scores([70, 50, 90], 60) == [70, 90]
    assert passing_scores([10, 20, 30], 25) == [30]
    # Empty input yields an empty list.
    assert passing_scores([], 50) == []
    # When every score is below the threshold, nothing passes.
    assert passing_scores([5, 4, 3], 100) == []
    # The result is a list.
    assert isinstance(passing_scores([80], 60), list)
