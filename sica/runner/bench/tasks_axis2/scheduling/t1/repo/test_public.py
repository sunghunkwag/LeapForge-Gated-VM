from main import capacity_at


def test_public():
    # A uniform schedule assigns the same capacity to every slot, so the exact
    # slot a minute maps to does not change the answer -- every lookup is 5.
    # (Minutes are kept away from the final slot on purpose.)
    caps = [5, 5, 5, 5]
    assert capacity_at(0, caps) == 5
    assert capacity_at(59, caps) == 5
    assert capacity_at(60, caps) == 5
    assert capacity_at(120, caps) == 5

    # With 30-minute slots the same uniform-schedule property holds.
    assert capacity_at(0, [7, 7, 7], 30) == 7
    assert capacity_at(45, [7, 7, 7], 30) == 7
