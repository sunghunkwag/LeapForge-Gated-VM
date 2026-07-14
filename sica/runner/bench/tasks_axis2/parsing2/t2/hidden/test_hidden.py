from main import parse_setting


def test_value_with_extra_colons_is_kept():
    assert parse_setting("host:localhost:8080") == ("host", "localhost:8080")
    assert parse_setting("k:a:b:c") == ("k", "a:b:c")


def test_url_value():
    assert parse_setting("endpoint:http://example.com:80") == (
        "endpoint", "http://example.com:80")


def test_key_is_only_before_first_colon():
    key, value = parse_setting("a:b:c")
    assert key == "a"
    assert value == "b:c"


def test_single_colon_still_parses():
    assert parse_setting("a:b") == ("a", "b")
    assert parse_setting("timeout:30") == ("timeout", "30")


def test_empty_value():
    assert parse_setting("k:") == ("k", "")
