from main import count_in_range


def test_public():
    # Cases where no value equals the upper bound -- inclusive vs exclusive
    # upper bound makes no difference here, so this passes either way.
    assert count_in_range([1, 2, 3, 4], 2, 5) == 3
    assert count_in_range([], 0, 10) == 0
    assert count_in_range([7, 8, 9], 0, 100) == 3
