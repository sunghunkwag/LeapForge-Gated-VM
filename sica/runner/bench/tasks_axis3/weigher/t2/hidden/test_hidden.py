from main import remaining_capacity


def test_load_reduces_remaining_capacity():
    assert remaining_capacity(100, [30, 20]) == 50
    assert remaining_capacity(50, [10, 10, 10]) == 20
    assert remaining_capacity(200, [75, 25]) == 100


def test_single_load():
    assert remaining_capacity(100, [40]) == 60
    assert remaining_capacity(10, [3]) == 7


def test_loaded_to_the_limit_leaves_zero():
    assert remaining_capacity(200, [200]) == 0
    assert remaining_capacity(90, [40, 50]) == 0


def test_empty_scale_still_full():
    assert remaining_capacity(100, []) == 100
    assert remaining_capacity(0, []) == 0
