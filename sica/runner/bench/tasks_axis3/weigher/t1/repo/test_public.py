from main import check


def test_check_returns_int():
    assert isinstance(check("a"), int)
    assert isinstance(check("word"), int)
    assert isinstance(check(""), int)


def test_check_is_deterministic():
    assert check("weigher") == check("weigher")
    assert check("abc") == check("abc")
