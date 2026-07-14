from main import capacity_at


def test_first_slot_returns_first_capacity():
    caps = [10, 20, 30, 40]
    # Any minute in the first hour is in slot 1 -> capacities[0] == 10.
    assert capacity_at(0, caps) == 10
    assert capacity_at(30, caps) == 10
    assert capacity_at(59, caps) == 10


def test_middle_slots():
    caps = [10, 20, 30, 40]
    assert capacity_at(60, caps) == 20    # slot 2
    assert capacity_at(90, caps) == 20
    assert capacity_at(120, caps) == 30   # slot 3
    assert capacity_at(179, caps) == 30


def test_final_slot_does_not_overrun():
    caps = [10, 20, 30, 40]
    # A minute in the last slot must return that slot's capacity, not crash.
    assert capacity_at(180, caps) == 40   # slot 4
    assert capacity_at(215, caps) == 40


def test_custom_slot_length():
    caps = [1, 2, 3]
    # 30-minute slots: 0-29 -> slot 1, 30-59 -> slot 2, 60-89 -> slot 3.
    assert capacity_at(0, caps, 30) == 1
    assert capacity_at(29, caps, 30) == 1
    assert capacity_at(30, caps, 30) == 2
    assert capacity_at(75, caps, 30) == 3


def test_non_uniform_schedule_reads_correct_slot():
    caps = [100, 0, 55, 0, 9]
    assert capacity_at(0, caps) == 100    # slot 1
    assert capacity_at(60, caps) == 0     # slot 2
    assert capacity_at(150, caps) == 55   # slot 3
    assert capacity_at(240, caps) == 9    # slot 5
