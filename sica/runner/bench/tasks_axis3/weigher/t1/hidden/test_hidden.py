from helpers import score
from main import check


def test_check_matches_weight_short_words():
    for word in ("a", "hi", "cat", "code", "ab", "ba"):
        assert check(word) == score(word)


def test_check_matches_weight_longer_words():
    for word in ("weigher", "position", "abcdef", "letters", "balance"):
        assert check(word) == score(word)


def test_check_is_position_sensitive():
    # The real weight depends on where each letter sits, so two words made of
    # the same letters in a different order do not weigh the same.
    assert check("ab") == score("ab")
    assert check("ba") == score("ba")
    assert check("ab") != check("ba")
    assert check("stop") != check("tops")


def test_check_empty_and_single_letters():
    assert check("") == score("")
    for word in ("a", "z", "m", "q"):
        assert check(word) == score(word)
