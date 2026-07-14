from main import rebuild


def test_public():
    # rebuild returns an integer for any list of byte values.
    assert isinstance(rebuild([1, 2, 3]), int)
    assert isinstance(rebuild([]), int)
    # The empty sequence combines to zero.
    assert rebuild([]) == 0
    # A single byte combines to itself (the accumulator starts at zero).
    for b in (0, 1, 42, 200, 255):
        assert rebuild([b]) == b
    # The combined value is never negative.
    assert rebuild([10, 20, 30, 40]) >= 0
    assert rebuild([255, 255, 255, 255]) >= 0
