from main import preview


def test_caps_to_character_count():
    # A cap of 3 characters keeps three characters, not three words.
    assert preview("the quick brown fox jumps", 3) == "the"
    assert preview("hello world", 3) == "hel"
    assert preview("alpha beta gamma delta", 5) == "alpha"


def test_single_long_word_is_cut_mid_word():
    # A single word longer than the cap is cut in the middle of the word.
    assert preview("abcdefgh", 4) == "abcd"
    assert preview("supercalifragilistic", 5) == "super"


def test_result_never_exceeds_char_limit():
    for text, n in [("alpha beta gamma", 4), ("one two three", 2),
                    ("xyzzy plugh", 3), ("abcdefghij", 6)]:
        assert len(preview(text, n)) <= n


def test_prefix_of_original_text():
    assert preview("abcdef", 6) == "abcdef"
    assert preview("abcdefghij", 6) == "abcdef"
    assert preview("greetings earthlings", 4) == "gree"


def test_zero_cap_is_empty():
    assert preview("anything at all", 0) == ""
    assert preview("word", 0) == ""
