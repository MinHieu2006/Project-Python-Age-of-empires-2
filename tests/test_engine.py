"""Tests du moteur : règles des sections 72 et 73 du sujet."""

import math

from engine.buildings.castle import Castle
from engine.constants import (
    CATAPHRACT, CAVALRY_ARCHER, LEGIONARY, PARTHIAN, ROMAN, TREBUCHET,
)
from engine.units.Elite_Cataphract import Elite_Cataphract
from engine.units.cavalry_archer import Cavalry_Archer
from engine.units.legionary import Legionary
from engine.units.trebuchet import Trebuchet
from engine.world import Order, World


def make_world():
    w = World(80, 80, seed=1)
    # un trébuchet loin de tout, pour que la partie ne s'arrête pas
    w.add_unit(Trebuchet(2, 2, ROMAN), TREBUCHET)
    return w


def hex_block(w, cx, cy, n_cols=5, n_rows=3, spacing=0.4):
    legs = []
    for r in range(n_rows):
        for c in range(n_cols):
            x = cx + c * spacing + (r % 2) * spacing / 2
            y = cy + r * spacing * math.sqrt(3) / 2
            legs.append(w.add_unit(Legionary(x, y, ROMAN), LEGIONARY))
    return legs


def test_shield_wall_depend_des_voisins():
    w = make_world()
    legs = hex_block(w, 10, 10)
    w.step()
    centre = legs[7]                       # 6 voisins au contact
    coin = legs[0]                         # 2 voisins seulement
    assert centre.shield_wall
    assert not coin.shield_wall
    assert centre.get_pierce_armour() == 12
    assert coin.get_pierce_armour() == 6


def test_shield_wall_perdu_quand_un_voisin_meurt():
    w = make_world()
    legs = [w.add_unit(Legionary(10 + dx, 10 + dy, ROMAN), LEGIONARY)
            for dx, dy in [(0, 0), (0.4, 0), (-0.4, 0), (0, 0.4), (0, -0.4)]]
    w.step()
    assert legs[0].shield_wall             # exactement 4 voisins
    legs[1].HP = 0
    w.step()
    w.step()
    assert not legs[0].shield_wall


def test_formule_de_degats():
    leg = Legionary(0, 0, ROMAN)
    assert leg.receive_attack(pierce_damage=12) == 6        # 12 - 6
    leg.shield_wall = True
    assert leg.receive_attack(pierce_damage=12) == 1        # max(1, 12 - 12)
    castle = Castle(40, 40)
    assert castle.receive_pierce_attack(200, 250) == 437


def test_pietinement_du_cataphracte():
    w = make_world()
    cata = w.add_unit(Elite_Cataphract(20, 20, PARTHIAN), CATAPHRACT)
    cible = w.add_unit(Legionary(20.45, 20, ROMAN), LEGIONARY)       # au contact
    voisin = w.add_unit(Legionary(20.3, 20.6, ROMAN), LEGIONARY)     # à 0.67 du centre
    loin = w.add_unit(Legionary(19.0, 20.0, ROMAN), LEGIONARY)       # à 1.0
    cata.order = Order("attack", target=cible)
    while cata.pending_target is None:
        w.step()
    w.run(until=w.time + 1.5)
    assert cible.HP == 75 - 8
    assert voisin.HP == 75 - 8
    assert loin.HP == 75


def test_archer_immobile_pendant_le_tir_et_projectile_visible():
    w = make_world()
    hca = w.add_unit(Cavalry_Archer(20, 20, PARTHIAN), CAVALRY_ARCHER)
    leg = w.add_unit(Legionary(26, 20, ROMAN), LEGIONARY)
    hca.order = Order("attack", target=leg)
    w.step()
    assert hca.is_busy_attacking(w.time)
    x0 = hca.x
    w.run(until=w.time + 1.0)
    assert hca.x == x0                     # pas de mouvement pendant 1.17 s
    w.run(until=w.time + 0.3)
    assert w.projectiles                   # la flèche est partie à la fin de l'animation
    w.run(until=w.time + 1.5)
    assert leg.HP == 75 - 6                # 12 - 6, flèche arrivée


def test_pas_de_chevauchement():
    w = make_world()
    units = [w.add_unit(Legionary(10 + i * 0.5, 10, ROMAN), LEGIONARY) for i in range(10)]
    for u in units:
        u.order = Order("move", 12, 10)
    w.run(until=10)
    for i, a in enumerate(units):
        for b in units[i + 1:]:
            assert math.hypot(a.x - b.x, a.y - b.y) >= 0.4 - 1e-6


def test_falaise_infranchissable():
    w = make_world()
    castle = w.add_castle(Castle(40, 40), PARTHIAN)
    leg = w.add_unit(Legionary(30, 40, ROMAN), LEGIONARY)
    leg.order = Order("attack", target=castle)
    w.run(until=5)
    assert leg.order is None               # pas d'attaque de mêlée sur le château
    leg.order = Order("move", 40, 40)
    w.run(until=60)
    assert w.map.circle_is_free(leg.x, leg.y, leg.unit_collision_radius)


def test_tir_du_chateau_par_volees_de_5():
    w = make_world()
    castle = w.add_castle(Castle(40, 40), PARTHIAN)
    leg = w.add_unit(Legionary(50, 40, ROMAN), LEGIONARY)     # bord du château à 8
    w.step()
    assert len(w.projectiles) == 5
    w.run(until=1.5)
    assert leg.HP == 75 - 5 * 9            # 5 flèches de 15 - 6


def test_trebuchet_detruit_le_chateau():
    w = World(80, 80, seed=3)
    castle = w.add_castle(Castle(40, 40), PARTHIAN)
    treb = w.add_unit(Trebuchet(40 - 17, 40, ROMAN), TREBUCHET)
    treb.order = Order("attack", target=castle)
    w.run()
    assert w.winner == ROMAN and not castle.is_alive()


def test_victoire_parthe_quand_les_trebuchets_meurent():
    w = make_world()
    w.add_castle(Castle(40, 40), PARTHIAN)
    for u in w.units_of(ROMAN, TREBUCHET):
        u.HP = 0
    w.step()
    assert w.over and w.winner == PARTHIAN
