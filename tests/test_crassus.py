"""Tests du général romain CRASSUS et des corrections de formation associées."""

from __future__ import annotations

import math

import pytest

from ai.parthian.surena import Surena
from ai.roman.crassus import Crassus, angle_diff
from ai.shared.braindead import Braindead
from engine.constants import LEGIONARY, ROMAN, SHIELD_WALL_DISTANCE
from engine.formations.formation import DENSE_SPACING, Formation, local_slots
from engine.units.legionary import Legionary
from engine.world import World
from scenarios.carrhae import Carrhae, build_world

LEGIONARY_DIAMETER = 0.4


def _neighbours(slots: list[tuple[float, float]]) -> list[int]:
    return [sum(1 for b in slots if b is not a and math.dist(a, b) <= SHIELD_WALL_DISTANCE)
            for a in slots]


@pytest.mark.parametrize("shape,n,ranks", [
    ("block", 22, 5), ("block", 8, 3), ("block", 7, 3), ("block", 16, 4),
    ("line", 21, 2), ("line", 22, 2), ("line", 9, 2),
])
def test_places_ne_se_chevauchent_pas(shape: str, n: int, ranks: int) -> None:
    """Un rang incomplet restait recentré d'une demi-place : il tombait à
    0.351 du rang voisin, place inaccessible (diamètre 0.40)."""
    slots = local_slots(shape, n, DENSE_SPACING, ranks)
    assert len(slots) == n
    closest = min(math.dist(a, b) for a in slots for b in slots if a is not b)
    assert closest >= LEGIONARY_DIAMETER


def test_ligne_dense_met_presque_tout_le_monde_en_shield_wall() -> None:
    slots = local_slots("line", 22, DENSE_SPACING, 2)
    assert sum(k >= 4 for k in _neighbours(slots)) >= 18      # seules les extrémités


def test_une_formation_large_pivote_au_pas_de_ses_unites() -> None:
    """Les extrémités d'une ligne qui pivote ne vont pas plus vite que les
    légionnaires : sinon elle se disloque."""
    w = World(seed=1)
    us = [Legionary(30 + i * 0.5, 30, ROMAN) for i in range(22)]
    for u in us:
        w.add_unit(u, LEGIONARY)
    f = Formation(w, us, shape="line", team=ROMAN, spacing=DENSE_SPACING, ranks=2)
    f.update(0.0)
    f.set_facing(f.facing + math.pi / 2)
    before = f.facing
    f.update(w.dt)
    turned = abs(f.facing - before)
    half_width = f.width() / 2
    assert turned * half_width <= us[0].speed * w.dt + 1e-9
    assert turned < f.turn_rate * w.dt


def test_angle_diff() -> None:
    assert angle_diff(0.1, 2 * math.pi + 0.1) == pytest.approx(0.0)
    assert angle_diff(math.pi - 0.1, -math.pi + 0.1) == pytest.approx(0.2)


def test_personne_a_portee_du_chateau() -> None:
    """Contre des Parthes immobiles, seul le château peut tuer : avant, il
    abattait une partie de l'écran pendant le siège."""
    r = Carrhae(Crassus(), Braindead(), seed=3, headless=True)
    assert r.winner == ROMAN
    assert not [loss for loss in r.losses if loss[2] == LEGIONARY]


def test_shield_wall_tenu_pendant_la_marche() -> None:
    w = build_world(Crassus(), Braindead(), seed=1)
    in_sw = total = 0
    while w.time < 70:
        w.step()
        if w.time < 20:          # mise en place
            continue
        for f in w.formations:
            if f.team == ROMAN and f.name in ("Escorte", "Écran") and f.is_dense():
                members = f.alive_members()
                in_sw += sum(u.shield_wall for u in members)
                total += len(members)
    assert total and in_sw / total >= 0.4


def test_escorte_ligne_puis_anneau_et_riposte() -> None:
    r = Carrhae(Crassus(), Surena(), seed=2, headless=True)
    texts = [text for _, text in r.decisions[ROMAN]]
    assert any("ANNEAU" in t for t in texts)
    assert any("3 contre 1" in t for t in texts)
    assert r.winner is not None


def test_parametres_et_repr() -> None:
    general = Crassus(aggressiveness=80, chase=False, melee_reach=1.5)
    assert "aggressiveness=80" in repr(general) and "chase=False" in repr(general)
    r = Carrhae(general, Braindead(), seed=1, n_legionaries=30, n_trebuchets=2,
                roman_start_position="N", headless=True)
    assert r.winner == ROMAN
