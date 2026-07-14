from core import net

def test_hidden():
    assert net(100, 2) == 90.0
    assert net(200, 3) == 150.0
    assert net(80, 1) == 80.0
