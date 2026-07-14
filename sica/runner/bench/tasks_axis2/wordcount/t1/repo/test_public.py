from main import preview


def test_public():
    # Empty text previews to the empty string for any cap.
    assert preview("", 10) == ""
    # When the cap is at least as large as the text, the whole text comes back
    # unchanged (single word, well within the character cap).
    assert preview("hello", 10) == "hello"
    assert preview("hi", 2) == "hi"
    # A short single-spaced phrase whose length is below the cap is returned in
    # full, unchanged.
    assert preview("one two three", 100) == "one two three"
    # The preview is always a string.
    assert isinstance(preview("hello", 3), str)
