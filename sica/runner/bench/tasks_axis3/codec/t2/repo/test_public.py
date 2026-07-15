from main import checksum


def test_checksum_contract():
    assert checksum([]) == 0
    assert isinstance(checksum([1, 2, 3]), int)
    assert 0 <= checksum([10, 20, 30]) < 256
