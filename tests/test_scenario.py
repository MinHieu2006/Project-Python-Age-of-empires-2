"""Tests du scénario Carrhae et des IA."""

from ai.parthian.surena import Surena
from ai.roman.crassus import Crassus
from ai.shared.bedlam import Bedlam
from ai.shared.braindead import Braindead
from engine.constants import PARTHIAN, ROMAN
from scenarios.carrhae import Carrhae, build_world


def test_mise_en_place():
    w = build_world(seed=1)
    c = w.castle
    assert (c.x, c.y) == (60, 60)
    assert len(w.units_of(ROMAN)) == 63 and len(w.units_of(PARTHIAN)) == 40
    for u in w.units_of(PARTHIAN):
        d = ((u.x - c.x) ** 2 + (u.y - c.y) ** 2) ** 0.5
        assert 10 <= d <= 20
    for u in w.units_of(ROMAN):
        assert u.x < 30 and u.y > 90           # coin ouest


def test_braindead_contre_braindead_match_nul():
    r = Carrhae(Braindead(), Braindead(), seed=1, headless=True)
    assert r.winner is None and "timeout" in r.reason


def test_ia_completes_sans_match_nul_et_resultat_complet():
    r = Carrhae(Crassus(), Surena(), seed=2, headless=True)
    assert r.winner in (ROMAN, PARTHIAN)
    assert len(r.units) == 103                 # 63 Romains + 40 Parthes
    assert r.decisions[ROMAN] and r.decisions[PARTHIAN]
    assert r.to_dict()["parameters"]["n_legionaries"] == 60


def test_parametres_du_scenario():
    r = Carrhae(Bedlam, Bedlam, n_legionaries=10, n_cataphracts=3, n_cavalry_archers=3,
                n_trebuchets=1, roman_start_position="N", map_size=(80, 80),
                seed=4, headless=True)
    assert r.winner in (ROMAN, PARTHIAN)
    assert r.parameters["map_size"] == (80, 80)


def test_deterministe_avec_une_graine():
    a = Carrhae(Crassus(), Surena(), seed=7, headless=True)
    b = Carrhae(Crassus(), Surena(), seed=7, headless=True)
    assert (a.winner, a.duration) == (b.winner, b.duration)
