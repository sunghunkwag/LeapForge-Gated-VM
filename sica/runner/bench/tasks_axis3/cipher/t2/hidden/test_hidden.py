from main import rotate


def test_forward_shift():
    assert rotate("abc", 1) == "bcd"
    assert rotate("hello", 3) == "khoor"


def test_wraps_around_z():
    assert rotate("xyz", 3) == "abc"
    assert rotate("z", 1) == "a"


def test_mixed_content_shifts_letters_only():
    assert rotate("a b c", 1) == "b c d"
    assert rotate("cat & dog", 2) == "ecv & fqi"


def test_larger_shift():
    assert rotate("abc", 25) == "zab"
    assert rotate("zebra", 1) == "afcsb"
