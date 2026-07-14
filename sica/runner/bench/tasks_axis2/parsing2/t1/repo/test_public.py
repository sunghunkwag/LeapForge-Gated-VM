from main import lookup


def test_public():
    # A key that is not present in the pairs falls back to the default.
    assert lookup(["a=1", "b=2"], "c") == 0
    assert lookup(["a=1", "b=2"], "z", default=-1) == -1
    # Empty input returns the default without inspecting any record.
    assert lookup([], "a") == 0
    assert lookup([], "a", default=7) == 7
    # Matching is done on the key field, so a wanted key that is absent from a
    # long list of pairs still yields the default.
    assert lookup(["p=10", "q=20", "r=30"], "s", default=99) == 99
