from engine.buildings.castle import Castle


def test_initialisation():
    castle = Castle(60, 60)

    assert castle.hp == 10000
    assert castle.pierce_armor == 13
    assert castle.attack_range == 11


def test_degats_trebuchet():
    castle = Castle(60, 60)

    damage = castle.receive_pierce_attack(200, 250)

    assert damage == 437
    assert castle.hp == 9563


def test_portee():
    castle = Castle(60, 60)

    assert castle.is_in_range(66, 68) is True
    assert castle.is_in_range(80, 80) is False


def test_rechargement():
    castle = Castle(60, 60)

    assert castle.fire(0, 66, 68) == 5
    assert castle.fire(1, 66, 68) == 0
    assert castle.fire(2, 66, 68) == 5


def test_chateau_detruit():
    castle = Castle(60, 60)

    castle.take_damage(10000)

    assert castle.is_destroyed() is True
    assert castle.fire(0, 66, 68) == 0