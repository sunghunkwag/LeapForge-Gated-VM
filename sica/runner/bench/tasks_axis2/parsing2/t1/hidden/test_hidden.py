from main import lookup


def test_returns_value_for_present_key():
    assert lookup(["a=1", "b=2"], "a") == 1
    assert lookup(["a=1", "b=2"], "b") == 2


def test_single_pair():
    assert lookup(["score=42"], "score") == 42


def test_first_match_wins():
    assert lookup(["k=1", "k=2"], "k") == 1


def test_value_among_many():
    pairs = ["p=10", "q=20", "r=30"]
    assert lookup(pairs, "p") == 10
    assert lookup(pairs, "q") == 20
    assert lookup(pairs, "r") == 30


def test_whitespace_around_fields():
    assert lookup([" x = 5 "], "x") == 5


def test_default_still_used_for_missing_key():
    assert lookup(["a=1", "b=2"], "c", default=-5) == -5
