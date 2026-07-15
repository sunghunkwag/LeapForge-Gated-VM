from main import count_long_words


def test_public():
    # Empty text has no long words.
    assert count_long_words("", 1) == 0
    # No word reaches the threshold, so the count is zero.
    assert count_long_words("x yy zzz", 5) == 0
    # Words strictly longer than the threshold are all counted (none sits
    # exactly on the boundary here).
    assert count_long_words("hello world", 3) == 2
    assert count_long_words("aa bbbb", 3) == 1
    assert count_long_words("aaaa bbbb", 2) == 2
