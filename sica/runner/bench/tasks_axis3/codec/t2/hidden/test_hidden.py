from main import checksum


def test_checksum_values():
    assert checksum([1, 2, 3]) == 6
    assert checksum([10, 20, 30]) == 60
    assert checksum([100, 100, 100]) == 44
    assert checksum([255, 1]) == 0
    assert checksum([]) == 0
