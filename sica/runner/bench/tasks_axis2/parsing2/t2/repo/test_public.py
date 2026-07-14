from main import parse_setting


def test_public():
    # A plain key:value with a single colon parses as expected.
    assert parse_setting("a:b") == ("a", "b")
    assert parse_setting("name:value") == ("name", "value")
    assert parse_setting("timeout:30") == ("timeout", "30")
    # An empty value (nothing after the colon) is allowed.
    assert parse_setting("k:") == ("k", "")
