"""Tests de l'API de formations (section 70 du sujet)."""

import math

from engine.constants import LEGIONARY, ROMAN, TREBUCHET
from engine.formations.formation import DENSE_SPACING, Formation, local_slots
from engine.units.legionary import Legionary
from engine.units.trebuchet import Trebuchet
from engine.world import World


def setup(n=12, x=10, y=10):
    w = World(80, 80, seed=1)
    w.add_unit(Trebuchet(2, 2, ROMAN), TREBUCHET)
    legs = [w.add_unit(Legionary(x + (i % 4) * 0.8, y + (i // 4) * 0.8, ROMAN), LEGIONARY)
            for i in range(n)]
    return w, legs


def test_places_dense_au_contact():
    slots = local_slots("block", 12, DENSE_SPACING, ranks=3)
    d = min(math.dist(a, b) for i, a in enumerate(slots) for b in slots[i + 1:])
    assert abs(d - DENSE_SPACING) < 1e-9
    assert len(local_slots("circle", 10, 0.8, radius=2.0)) == 10
    assert len(local_slots("wedge", 7, 0.6)) == 7


def test_la_formation_avance_groupee():
    w, legs = setup()
    f = Formation(w, legs, shape="line", ranks=2, spacing=1.0)
    w.formations.append(f)
    f.move_to(25, 10)
    w.run(until=30)
    assert math.hypot(f.x - 25, f.y - 10) < 0.1
    assert f.cohesion() < 0.3


def test_se_reforme_apres_des_pertes():
    w, legs = setup()
    f = Formation(w, legs, shape="line", ranks=2, spacing=1.0)
    w.formations.append(f)
    w.run(until=15)
    for u in legs[:4]:
        u.HP = 0
    w.run(until=30)
    assert f.size == 8
    assert len(f.slots_world) == 8
    assert f.cohesion() < 0.3


def test_split_et_merge():
    w, legs = setup()
    f = Formation(w, legs, shape="block", spacing=1.0)
    w.formations.append(f)
    parts = f.split(2)
    assert len(parts) == 2 and parts[0].size + parts[1].size == 12
    parts[0].merge(parts[1])
    assert parts[0].size == 12 and parts[1] not in w.formations


def test_place_between_et_cercle():
    w, legs = setup()
    f = Formation(w, legs, shape="line", spacing=1.0)
    w.formations.append(f)
    f.place_between((10, 10), (30, 10), 5)
    assert f.goal == (15, 10)
    f.circle_around((20, 20), radius=3)
    w.run(until=40)
    for u in legs:
        assert abs(math.hypot(u.x - 20, u.y - 20) - 3) < 0.3


def test_detach_rend_la_main_a_l_ia():
    w, legs = setup()
    f = Formation(w, legs, shape="line", spacing=1.0)
    w.formations.append(f)
    f.detach(legs[0], 5.0)
    w.step()
    assert legs[0].order is None
    w.run(until=6)
    assert legs[0].order is not None
