import random

from engine.buildings.castle import Castle
from engine.units.base_unit import BaseUnit
from engine.units.trebuchet import (
    PACKED, PACKING, UNPACKED, UNPACKING, Trebuchet,
)


class AlwaysHit(random.Random):
    def random(self):
        return 0.0


class AlwaysMiss(random.Random):
    def random(self):
        return 0.999


def deployed_treb(x=0, y=0, rng=None):
    treb = Trebuchet(x, y, "roman", rng=rng or AlwaysHit())
    treb.unpack(0)
    treb.update(11)
    return treb


def test_stats():
    t = Trebuchet(0, 0, "roman")
    assert t.HP == 150
    assert t.Pierce_attack == 200
    assert t.Melee_armour == 2
    assert t.Pierce_armour == 8
    assert t.range == 16
    assert t.min_range == 4
    assert t.speed == 0.80
    assert t.reload_time == 10
    assert t.attack_animation == 1.0
    assert t.unit_collision_radius == 0.50
    assert t.state == PACKED


def test_deploiement_11s():
    t = Trebuchet(0, 0, "roman")
    assert t.unpack(0)
    assert t.state == UNPACKING
    t.update(10.9)
    assert t.state == UNPACKING
    t.update(11)
    assert t.state == UNPACKED


def test_repli_11s():
    t = deployed_treb()
    assert t.pack(20)
    assert t.state == PACKING
    t.update(30.9)
    assert t.state == PACKING
    t.update(31)
    assert t.state == PACKED


def test_deplacement_seulement_replie():
    t = Trebuchet(0, 0, "roman")
    t.move_towards(10, 0, 1.0)
    assert t.x == 0.80

    t.unpack(1)
    t.move_towards(10, 0, 1.0, 1.5)   # en déploiement
    assert t.x == 0.80
    t.update(12)
    t.move_towards(10, 0, 1.0, 12)    # déployé
    assert t.x == 0.80


def test_pas_de_tir_replie():
    t = Trebuchet(0, 0, "roman", rng=AlwaysHit())
    castle = Castle(10, 0)
    assert t.attack(castle, 0) is False


def test_portee_min_et_max():
    t = deployed_treb()
    # La portée se mesure au bord du château (emprise 4x4 -> rayon 2)
    assert t.is_in_range(Castle(18, 0)) is True       # bord à 16
    assert t.is_in_range(Castle(18.5, 0)) is False    # bord à 16.5
    assert t.is_in_range(Castle(6, 0)) is True        # bord à 4
    assert t.is_in_range(Castle(5, 0)) is False       # bord à 3 < portée min


def test_degats_chateau_en_fin_animation():
    t = deployed_treb()
    castle = Castle(15, 0)
    assert t.attack(castle, 11)
    # Rien ne part pendant l'animation
    assert t.update(11.5) is None
    assert castle.HP == 10000
    shot = t.update(12)
    assert shot.hit and shot.damage == 437   # 200-13 + 250
    assert castle.HP == 10000 - 437


def test_rechargement_10s():
    t = deployed_treb()
    castle = Castle(15, 0)
    assert t.attack(castle, 11)
    t.update(12)
    assert t.attack(castle, 20) is False
    assert t.attack(castle, 21) is True


def test_immobile_pendant_animation():
    t = deployed_treb()
    t.attack(Castle(15, 0), 11)
    assert t.is_busy_attacking(11.5)
    assert t.pack(11.5) is True      # le repli annule le tir
    assert t.update(12) is None


def test_degats_contre_unite_sans_bonus():
    t = deployed_treb()
    leg = BaseUnit(8, 0, "parthian", hp=75, pierce_armour=6)
    t.attack(leg, 11)
    shot = t.update(12)
    assert shot.damage == 194
    assert not leg.is_alive()


def test_tir_rate():
    t = deployed_treb(rng=AlwaysMiss())
    castle = Castle(15, 0)
    t.attack(castle, 11)
    shot = t.update(12)
    assert shot.hit is False
    assert castle.HP == 10000


def test_precision_statistique():
    rng = random.Random(42)
    hits = 0
    n = 2000
    for _ in range(n):
        t = deployed_treb(rng=rng)
        t.attack(Castle(15, 0), 11)
        hits += t.update(12).hit
    assert 0.77 < hits / n < 0.83


def test_trebuchet_peut_etre_tue():
    t = Trebuchet(0, 0, "roman")
    t.receive_attack(pierce_damage=12)   # flèche d'archer à cheval
    assert t.HP == 146
    t.HP = 0
    assert not t.is_alive()
    assert t.unpack(0) is False
