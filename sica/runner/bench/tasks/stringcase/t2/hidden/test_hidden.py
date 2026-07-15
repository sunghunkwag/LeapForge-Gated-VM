"""Hidden grading tests for title_case (the fail->pass signal)."""
from core import title_case


def test_last_word_minor_is_capitalized():
    # The final word is always capitalized, even when it is a minor word.
    assert title_case("something to hold on to") == "Something to Hold on To"
    assert title_case("this is the way in") == "This Is the Way In"
    assert title_case("what are you waiting for") == "What Are You Waiting For"


def test_first_word_minor_is_capitalized():
    assert title_case("of mice and men") == "Of Mice and Men"
    assert title_case("to be or not to be") == "To Be or Not to Be"
    assert title_case("the day") == "The Day"


def test_interior_minor_words_stay_lowercase():
    assert title_case("the lord of the rings") == "The Lord of the Rings"
    assert title_case("gone with the wind") == "Gone with the Wind"


def test_single_minor_word_is_capitalized():
    # A one-word title is both the first and the last word.
    assert title_case("the") == "The"
    assert title_case("of") == "Of"


def test_mixed_case_input_normalized():
    assert title_case("PYTHON is FUN") == "Python Is Fun"
