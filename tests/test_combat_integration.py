from engine.game_engine import GameEngine


class AlwaysHit:
    def random(self):
        return 0.0


def test_trebuchet_castle_integration():
    game = GameEngine()

    game.setup_scenario(
        n_legionaries=0,
        n_trebuchets=1,
        n_elite_cataphracts=0,
        n_cavalry_archers=0
    )

    castle = game.castle
    trebuchet = game.romans[0]

    trebuchet.x = 45
    trebuchet.y = 60
    trebuchet.rng = AlwaysHit()

    assert trebuchet.unpack(0) is True

    game.step(11)

    assert trebuchet.is_unpacked() is True
    assert trebuchet.attack(castle, 11) is True

    game.step(0.5)
    assert castle.hp == 10000

    game.step(0.5)

    assert castle.hp == 9563
    assert len(game.shots_this_tick) == 1