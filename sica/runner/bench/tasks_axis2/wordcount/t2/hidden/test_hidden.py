from main import count_long_words


def test_word_exactly_min_len_counts():
    # Words whose length is exactly min_len must be counted.
    assert count_long_words("cat dog", 3) == 2
    assert count_long_words("io ok go", 2) == 3
    assert count_long_words("a", 1) == 1


def test_mixed_lengths_include_boundary():
    # lengths 1, 2, 3, 4 with min_len 2 -> bb, ccc, dddd all count.
    assert count_long_words("a bb ccc dddd", 2) == 3
    # lengths 1, 2, 3 with min_len 1 -> every word counts.
    assert count_long_words("a ab abc", 1) == 3


def test_boundary_and_above():
    # aaaa (4) meets min_len 4; bb (2) and c (1) fall short.
    assert count_long_words("aaaa bb c", 4) == 1
    # Both five-letter words meet a threshold of exactly five.
    assert count_long_words("hello world", 5) == 2


def test_below_threshold_excluded():
    # Nothing reaches the threshold, so the boundary rule changes nothing.
    assert count_long_words("a bb", 3) == 0
    assert count_long_words("one two", 4) == 0
