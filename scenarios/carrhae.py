"""Scénario 1 : Carrhae (section 71 du sujet).

Utilisation :

    from scenarios.carrhae import Carrhae
    from ai.roman.crassus import Crassus
    from ai.parthian.surena import Surena

    result = Carrhae(roman_ai=Crassus(), parthian_ai=Surena(),
                     n_legionaries=60, n_cataphracts=20, n_cavalry_archers=20,
                     n_trebuchets=3, roman_start_position="W",
                     seed=1234, map_size=(120, 120), headless=False, speed=1)
    print(result.winner, result.reason)
"""

import math
import random
from dataclasses import asdict, dataclass, field

from engine.buildings.castle import Castle
from engine.constants import (
    CATAPHRACT, CAVALRY_ARCHER, DEFAULT_DT, DEFAULT_IDLE_TIMEOUT,
    DEFAULT_MAX_TIME, LEGIONARY, PARTHIAN, ROMAN, TREBUCHET,
)
from engine.units.Elite_Cataphract import Elite_Cataphract
from engine.units.cavalry_archer import Cavalry_Archer
from engine.units.legionary import Legionary
from engine.units.trebuchet import Trebuchet
from engine.world import World

# Coins de la carte en vue isométrique : (0, 0) est en haut (nord)
CORNERS = {
    "N": (0.0, 0.0),
    "E": (1.0, 0.0),
    "S": (1.0, 1.0),
    "W": (0.0, 1.0),
}
CORNER_MARGIN = 9.0


@dataclass
class BattleResult:
    winner: str                 # "ROMAN", "PARTHIAN" ou None (match nul)
    reason: str
    duration: float             # secondes de jeu
    seed: object
    roman_ai: str
    parthian_ai: str
    parameters: dict
    units: list                 # état final de chaque unité
    losses: list                # (temps, id, type, camp)
    decisions: dict             # camp -> [(temps, texte)]
    damage_dealt: dict
    castle_hp: int
    survivors: dict = field(default_factory=dict)

    @property
    def is_draw(self):
        return self.winner is None

    def to_dict(self):
        return asdict(self)

    def summary(self):
        w = self.winner or "MATCH NUL"
        s = self.survivors
        return (f"{w} ({self.reason}) en {self.duration:.0f} s | "
                f"{self.roman_ai} vs {self.parthian_ai} | "
                f"survivants R {s.get(ROMAN, {})} / P {s.get(PARTHIAN, {})} | "
                f"château {self.castle_hp} PV")


def _make_general(ai, default):
    if ai is None:
        ai = default
    if isinstance(ai, type):
        ai = ai()
    return ai


def _place(world, rng, unit_factory, n, cx, cy, sampler, placed):
    """Place n unités sans chevauchement (les armées ne commencent pas en
    formation)."""
    units = []
    for _ in range(n):
        for _attempt in range(500):
            x, y = sampler(rng, cx, cy)
            probe = unit_factory(x, y)
            r = probe.unit_collision_radius
            if not world.map.circle_is_free(x, y, r + 0.05):
                continue
            if any(math.hypot(o.x - x, o.y - y) < r + o.unit_collision_radius + 0.1
                   for o in placed):
                continue
            placed.append(probe)
            units.append(probe)
            break
    return units


def build_world(roman_ai=None, parthian_ai=None, n_legionaries=60, n_cataphracts=20,
                n_cavalry_archers=20, n_trebuchets=3, roman_start_position="W",
                seed=None, map_size=(120, 120), idle_timeout=DEFAULT_IDLE_TIMEOUT,
                max_time=DEFAULT_MAX_TIME, dt=DEFAULT_DT):
    from ai.parthian.surena import Surena
    from ai.roman.crassus import Crassus

    width, height = map_size
    world = World(width, height, seed=seed, dt=dt, idle_timeout=idle_timeout,
                  max_time=max_time)
    rng = random.Random(seed)

    castle = Castle(world.map.cx, world.map.cy)
    world.add_castle(castle, PARTHIAN)

    # Point de départ romain : un coin (ou des coordonnées explicites)
    if isinstance(roman_start_position, str):
        fx, fy = CORNERS[roman_start_position.upper()]
        rx = CORNER_MARGIN + fx * (width - 2 * CORNER_MARGIN)
        ry = CORNER_MARGIN + fy * (height - 2 * CORNER_MARGIN)
    else:
        rx, ry = roman_start_position

    placed = []
    n_total = n_legionaries + n_trebuchets
    spawn_r = max(4.0, math.sqrt(n_total) * 0.9)

    def roman_sampler(rng, cx, cy):
        a = rng.uniform(0, 2 * math.pi)
        d = spawn_r * math.sqrt(rng.random())
        return cx + d * math.cos(a), cy + d * math.sin(a)

    # Les Parthes : autour du château, à 10-20 cases, côté Romains
    toward = math.atan2(ry - castle.y, rx - castle.x)

    def parthian_sampler(rng, cx, cy):
        a = toward + rng.uniform(-1.0, 1.0)
        d = rng.uniform(10.0, 20.0)
        return cx + d * math.cos(a), cy + d * math.sin(a)

    trebs = _place(world, rng, lambda x, y: Trebuchet(x, y, ROMAN), n_trebuchets,
                   rx, ry, lambda rng, cx, cy: roman_sampler(rng, cx, cy), placed)
    legs = _place(world, rng, lambda x, y: Legionary(x, y, ROMAN), n_legionaries,
                  rx, ry, roman_sampler, placed)
    catas = _place(world, rng, lambda x, y: Elite_Cataphract(x, y, PARTHIAN), n_cataphracts,
                   castle.x, castle.y, parthian_sampler, placed)
    hcas = _place(world, rng, lambda x, y: Cavalry_Archer(x, y, PARTHIAN), n_cavalry_archers,
                  castle.x, castle.y, parthian_sampler, placed)

    for u in trebs:
        world.add_unit(u, TREBUCHET)
    for u in legs:
        world.add_unit(u, LEGIONARY)
    for u in catas:
        world.add_unit(u, CATAPHRACT)
    for u in hcas:
        world.add_unit(u, CAVALRY_ARCHER)

    world.set_general(ROMAN, _make_general(roman_ai, Crassus))
    world.set_general(PARTHIAN, _make_general(parthian_ai, Surena))
    return world


def make_result(world, params):
    units = []
    survivors = {ROMAN: {}, PARTHIAN: {}}
    for u in world.all_units:
        alive = u.is_alive()
        units.append({
            "id": u.uid, "type": u.kind, "team": u.team,
            "hp": u.HP, "max_hp": u.max_hp, "alive": alive,
            "x": round(u.x, 2), "y": round(u.y, 2),
            "death_time": u.death_time,
        })
        if alive:
            survivors[u.team][u.kind] = survivors[u.team].get(u.kind, 0) + 1
    decisions = {}
    for t, team, _name, text in world.decision_log:
        decisions.setdefault(team, []).append((t, text))
    r_gen = world.generals.get(ROMAN, (None,))[0]
    p_gen = world.generals.get(PARTHIAN, (None,))[0]
    return BattleResult(
        winner=world.winner, reason=world.end_reason or "en cours",
        duration=round(world.time, 2), seed=world.seed,
        roman_ai=repr(r_gen), parthian_ai=repr(p_gen), parameters=params,
        units=units, losses=list(world.losses), decisions=decisions,
        damage_dealt=dict(world.damage_dealt),
        castle_hp=world.castle.HP if world.castle else 0,
        survivors=survivors,
    )


def Carrhae(roman_ai=None, parthian_ai=None, n_legionaries=60, n_cataphracts=20,
            n_cavalry_archers=20, n_trebuchets=3, roman_start_position="W",
            seed=None, map_size=(120, 120), headless=False, speed=1,
            idle_timeout=DEFAULT_IDLE_TIMEOUT, max_time=DEFAULT_MAX_TIME,
            dt=DEFAULT_DT):
    """Lance la bataille de Carrhae et renvoie un BattleResult.

    roman_ai / parthian_ai : une instance ou une classe de General
    (par défaut Crassus et Surena). headless=True : pas de fenêtre,
    simulation aussi rapide que possible."""
    params = dict(n_legionaries=n_legionaries, n_cataphracts=n_cataphracts,
                  n_cavalry_archers=n_cavalry_archers, n_trebuchets=n_trebuchets,
                  roman_start_position=roman_start_position, map_size=tuple(map_size))
    world = build_world(roman_ai, parthian_ai, n_legionaries, n_cataphracts,
                        n_cavalry_archers, n_trebuchets, roman_start_position,
                        seed, map_size, idle_timeout, max_time, dt)
    if headless:
        world.run()
    else:
        from visualisation.gui.view import run_view
        run_view(world, speed=speed)
    return make_result(world, params)
