"""Public tests for title_case.

Every case here already passes on the shipped code (each title's final word is
a major word, so it is capitalized regardless of the bug). They pin down the
general behaviour: major words capitalized, interior minor words lowercased,
the first word always capitalized, and mixed-case input normalized.
"""
from core import title_case


def test_major_and_minor_words():
    assert title_case("the lord of the rings") == "The Lord of the Rings"
    assert title_case("a tale of two cities") == "A Tale of Two Cities"


def test_interior_minor_words_lowercased():
    assert title_case("gone with the wind") == "Gone with the Wind"


def test_first_word_always_capitalized():
    assert title_case("of mice and men") == "Of Mice and Men"


def test_input_case_is_normalized():
    assert title_case("PYTHON is FUN") == "Python Is Fun"


def test_single_major_word():
    assert title_case("hello") == "Hello"


def test_empty_string():
    assert title_case("") == ""
