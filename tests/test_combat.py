from engine.combat.combat import apply_pierce_attack
from engine.buildings.castle import Castle
from engine.units.trebuchet import Trebuchet

from engine.combat.combat import calculate_pierce_damage


def test_normal_attack():
    assert calculate_pierce_damage(20, 13) == 7


def test_trebuchet_vs_castle():
    assert calculate_pierce_damage(200, 13, 250) == 437


def test_minimum_damage():
    assert calculate_pierce_damage(5, 13) == 1

def test_trebuchet_damages_castle():
    castle = Castle(60, 60)
    trebuchet = Trebuchet(45, 60, "Romans")

    damage = apply_pierce_attack(
        trebuchet,
        castle,
        bonus=250
    )

    assert damage == 437
    assert castle.hp == 9563    