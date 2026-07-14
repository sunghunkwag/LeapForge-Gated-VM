from main import fulfill


def test_public():
    # Ordinary partial orders leave a positive remainder in stock.
    assert fulfill(10, 3) == 7
    assert fulfill(5, 1) == 4
    assert fulfill(100, 40) == 60
