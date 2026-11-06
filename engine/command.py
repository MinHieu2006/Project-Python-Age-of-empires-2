"""Interface entre une IA (un « général ») et le moteur.

Une IA ne modifie jamais les unités directement : elle donne des ordres
individuels ou crée des formations par l'intermédiaire de ce Commander,
qui ne la laisse commander que son propre camp."""

import math

from engine.formations.formation import Formation
from engine.world import Order, edge_distance


class Commander:
    def __init__(self, world, team, general):
        self.world = world
        self.team = team
        self.general = general

    # ------------------------------------------------------------------
    # Lecture de l'état (pas de brouillard de guerre)
    # ------------------------------------------------------------------
    @property
    def time(self):
        return self.world.time

    @property
    def map(self):
        return self.world.map

    @property
    def castle(self):
        return self.world.castle

    def my_units(self, kind=None):
        return self.world.units_of(self.team, kind)

    def enemy_units(self, kind=None):
        return self.world.enemies_of(self.team, kind)

    def my_formations(self):
        return [f for f in self.world.formations if f.team == self.team]

    @staticmethod
    def distance(a, b):
        return math.hypot(a.x - b.x, a.y - b.y)

    @staticmethod
    def edge_distance(unit, target):
        return edge_distance(unit, target)

    @staticmethod
    def centroid(units):
        units = list(units)
        if not units:
            return None
        return (sum(u.x for u in units) / len(units),
                sum(u.y for u in units) / len(units))

    def nearest(self, x, y, units):
        best, bd = None, math.inf
        for u in units:
            d = (u.x - x) ** 2 + (u.y - y) ** 2
            if d < bd:
                best, bd = u, d
        return best, math.sqrt(bd) if best is not None else math.inf

    # ------------------------------------------------------------------
    # Ordres individuels
    # ------------------------------------------------------------------
    def _check(self, unit):
        if unit.team != self.team:
            raise ValueError("une IA ne peut commander que son propre camp")

    def move(self, unit, x, y, engage=0.0, leash=0.0, prefer=()):
        self._check(unit)
        x, y = self.world.map.clamp(x, y, unit.unit_collision_radius)
        unit.order = Order("move", x, y, engage=engage, leash=leash, prefer=tuple(prefer))

    def attack(self, unit, target):
        self._check(unit)
        unit.order = Order("attack", target=target)

    def stop(self, unit):
        self._check(unit)
        unit.order = None

    # ------------------------------------------------------------------
    # Formations
    # ------------------------------------------------------------------
    def formation(self, units, shape="block", name="", **kwargs):
        for u in units:
            self._check(u)
        f = Formation(self.world, units, shape=shape, team=self.team,
                      name=name, **kwargs)
        self.world.formations.append(f)
        return f

    def disband(self, formation):
        formation.disband()

    # ------------------------------------------------------------------
    # Journal des décisions (rendu dans les résultats de la bataille)
    # ------------------------------------------------------------------
    def log(self, text):
        self.world.log_decision(self.team, self.general.name, text)
