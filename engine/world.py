"""Moteur de simulation : temps continu, positions flottantes, collisions
circulaires, combat (sections 72 et 73 du sujet)."""

import math
import random
from dataclasses import dataclass

from engine.constants import (
    ARROW_SPEED, CAVALRY_ARCHER, CASTLE, CATAPHRACT, DEFAULT_DT,
    DEFAULT_IDLE_TIMEOUT, DEFAULT_MAX_TIME, FIRST_CONTACT_TIMEOUT, LEGIONARY,
    MELEE_CONTACT_GAP,
    MELEE_RELEASE_GAP, PARTHIAN, ROMAN, SHIELD_WALL_DISTANCE,
    SHIELD_WALL_NEIGHBOURS, STONE_SPEED, TRAMPLE_RADIUS, TREBUCHET,
)
from engine.map.battlefield import Battlefield


# ----------------------------------------------------------------------
# Ordres individuels
# ----------------------------------------------------------------------
@dataclass
class Order:
    """Ordre donné à UNE unité. Les formations se traduisent en ordres
    individuels de ce type."""
    kind: str                  # "move" ou "attack"
    x: float = 0.0
    y: float = 0.0
    target: object = None
    engage: float = 0.0        # rayon d'engagement automatique (0 = jamais)
    leash: float = 0.0         # distance max à (x, y) pour engager (0 = sans limite)
    prefer: tuple = ()         # types de cibles prioritaires à l'engagement


@dataclass
class Projectile:
    kind: str                  # "arrow" ou "stone"
    team: str
    x: float
    y: float
    sx: float
    sy: float
    tx: float
    ty: float
    target: object
    speed: float
    pierce: int
    bonus: int
    hit: bool
    homing: bool
    t0: float
    alive: bool = True

    @property
    def progress(self):
        total = math.hypot(self.tx - self.sx, self.ty - self.sy)
        if total < 1e-6:
            return 1.0
        return min(1.0, math.hypot(self.x - self.sx, self.y - self.sy) / total)


# ----------------------------------------------------------------------
# Grille spatiale (recherche rapide des voisins)
# ----------------------------------------------------------------------
class SpatialGrid:
    def __init__(self, cell=1.5):
        self.cell = cell
        self.cells = {}

    def rebuild(self, units):
        self.cells = {}
        c = self.cell
        for u in units:
            key = (int(u.x // c), int(u.y // c))
            self.cells.setdefault(key, []).append(u)

    def near(self, x, y, radius):
        c = self.cell
        x0, x1 = int((x - radius) // c), int((x + radius) // c)
        y0, y1 = int((y - radius) // c), int((y + radius) // c)
        cells = self.cells
        for i in range(x0, x1 + 1):
            for j in range(y0, y1 + 1):
                bucket = cells.get((i, j))
                if bucket:
                    yield from bucket


def target_radius(target):
    if getattr(target, "is_building", False):
        return getattr(target, "footprint", 0) / 2.0
    return getattr(target, "unit_collision_radius", 0.0)


def edge_distance(unit, target):
    """Distance du centre de `unit` au bord de `target`."""
    return max(0.0, math.hypot(target.x - unit.x, target.y - unit.y)
               - target_radius(target))


# Angles d'évitement essayés quand le chemin direct est bloqué
_DETOURS = [0.0, 0.35, -0.35, 0.8, -0.8, 1.25, -1.25, 1.65, -1.65]
_DETOURS_CS = [(math.cos(a), math.sin(a)) for a in _DETOURS]


class World:
    def __init__(self, width=120, height=120, seed=None, dt=DEFAULT_DT,
                 idle_timeout=DEFAULT_IDLE_TIMEOUT, max_time=DEFAULT_MAX_TIME,
                 first_contact_timeout=FIRST_CONTACT_TIMEOUT):
        self.map = Battlefield(width, height)
        self.seed = seed
        self.rng = random.Random(seed)
        self.dt = dt
        self.time = 0.0
        self.idle_timeout = idle_timeout
        self.first_contact_timeout = max(first_contact_timeout, idle_timeout)
        self.first_damage_done = False
        self.max_time = max_time

        self.units = []            # unités vivantes
        self.all_units = []        # toutes les unités, mortes comprises
        self.castle = None
        self.projectiles = []
        self.corpses = []          # (x, y, kind, team, time)
        self.formations = []
        self.grid = SpatialGrid()

        self.generals = {}         # team -> (general, commander)
        self._next_decision = {}
        self._initial_trebuchets = 0

        self.last_damage_time = 0.0
        self.damage_dealt = {ROMAN: 0, PARTHIAN: 0}
        self.losses = []           # (time, uid, kind, team)
        self.decision_log = []     # (time, team, general, text)

        self._blocked = None
        self.over = False
        self.winner = None
        self.end_reason = None
        self._uid = 0

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def _next_uid(self):
        self._uid += 1
        return self._uid

    def add_unit(self, unit, kind):
        unit.uid = self._next_uid()
        unit.kind = kind
        unit.order = None
        unit.pending_target = None
        unit.release_time = 0.0
        unit.engaged = None
        unit.next_scan = 0.0
        unit.prev_x, unit.prev_y = unit.x, unit.y
        unit.facing = 0.0
        unit.moving = False
        unit.formation = None
        unit.last_hit_time = -10.0
        unit.death_time = None
        if not hasattr(unit, "shield_wall"):
            unit.shield_wall = False
        if kind == TREBUCHET:
            unit.rng = self.rng
            self._initial_trebuchets += 1
        self.units.append(unit)
        self.all_units.append(unit)
        return unit

    def add_castle(self, castle, team=PARTHIAN):
        castle.uid = self._next_uid()
        castle.kind = CASTLE
        castle.team = team
        castle.last_hit_time = -10.0
        self.castle = castle
        return castle

    def set_general(self, team, general):
        from engine.command import Commander
        cmd = Commander(self, team, general)
        self.generals[team] = (general, cmd)
        self._next_decision[team] = 0.0
        return cmd

    # ------------------------------------------------------------------
    # Requêtes
    # ------------------------------------------------------------------
    def units_of(self, team, kind=None):
        return [u for u in self.units
                if u.team == team and (kind is None or u.kind == kind)]

    def enemies_of(self, team, kind=None):
        return [u for u in self.units
                if u.team != team and (kind is None or u.kind == kind)]

    def log_decision(self, team, general_name, text):
        self.decision_log.append((round(self.time, 2), team, general_name, text))

    # ------------------------------------------------------------------
    # Boucle principale
    # ------------------------------------------------------------------
    def step(self):
        if self.over:
            return
        dt = self.dt
        t = self.time + dt
        self.time = t
        for u in self.units:
            u.prev_x, u.prev_y = u.x, u.y

        self.grid.rebuild(self.units)
        self._update_shield_walls()
        self._run_generals(t)
        for f in list(self.formations):
            f.update(t)
        self._resolve_trebuchets(t)
        self._resolve_pending_attacks(t)
        self._castle_fire(t)
        self._blocked = []
        for u in self.units:
            if u.is_alive():
                self._behave(u, t, dt)
        # Déplacements « simultanés » : une unité bloquée par une voisine qui
        # n'avait pas encore bougé retente sa chance une fois les autres passées.
        for _ in range(2):
            retry, self._blocked = self._blocked, []
            for u, gx, gy, chase in retry:
                self._move_unit(u, gx, gy, dt, chase)
            if not self._blocked:
                break
        self._blocked = []
        self._update_projectiles(t, dt)
        self._remove_dead(t)
        self._check_end(t)

    def run(self, until=None):
        while not self.over and (until is None or self.time < until):
            self.step()

    # ------------------------------------------------------------------
    # Shield Wall : propriété de chaque légionnaire et de la géométrie,
    # recalculée à chaque pas (10 fois par seconde)
    # ------------------------------------------------------------------
    def _update_shield_walls(self):
        d2max = SHIELD_WALL_DISTANCE ** 2
        for u in self.units:
            if u.kind != LEGIONARY:
                continue
            n = 0
            for o in self.grid.near(u.x, u.y, SHIELD_WALL_DISTANCE):
                if (o is not u and o.kind == LEGIONARY and o.team == u.team
                        and (o.x - u.x) ** 2 + (o.y - u.y) ** 2 <= d2max):
                    n += 1
            u.shield_wall = n >= SHIELD_WALL_NEIGHBOURS

    # ------------------------------------------------------------------
    # Généraux (IA)
    # ------------------------------------------------------------------
    def _run_generals(self, t):
        for team, (general, cmd) in self.generals.items():
            if t + 1e-9 < self._next_decision[team]:
                continue
            self._next_decision[team] = t + general.decision_interval
            try:
                if not getattr(general, "_ready", False):
                    general._ready = True
                    general.setup(cmd)
                general.decide(cmd)
            except Exception as exc:   # une IA défectueuse ne doit pas tout planter
                self.log_decision(team, general.name, f"ERREUR IA : {exc!r}")

    # ------------------------------------------------------------------
    # Combat
    # ------------------------------------------------------------------
    def _damage(self, team, target, melee=0, pierce=0, bonus=0):
        if not target.is_alive():
            return 0
        if getattr(target, "is_building", False):
            dmg = target.receive_pierce_attack(pierce, bonus)
        else:
            dmg = target.receive_attack(melee_damage=melee, pierce_damage=pierce)
        target.last_hit_time = self.time
        self.last_damage_time = self.time
        self.first_damage_done = True
        self.damage_dealt[team] = self.damage_dealt.get(team, 0) + dmg
        return dmg

    def in_attack_range(self, u, target):
        if u.range <= 0:
            gap = (math.hypot(target.x - u.x, target.y - u.y)
                   - u.unit_collision_radius - target_radius(target))
            return gap <= MELEE_CONTACT_GAP
        return edge_distance(u, target) <= u.range

    def _start_attack(self, u, target, t):
        u.pending_target = target
        u.release_time = t + u.attack_animation
        u.is_attacking_until = u.release_time
        u.next_attack_time = t + u.reload_time
        u.facing = math.atan2(target.y - u.y, target.x - u.x)

    def _resolve_pending_attacks(self, t):
        for u in self.units:
            target = u.pending_target
            if target is None or u.kind == TREBUCHET or t + 1e-9 < u.release_time:
                continue
            u.pending_target = None
            if not u.is_alive() or not target.is_alive():
                continue
            if u.range <= 0:
                gap = (math.hypot(target.x - u.x, target.y - u.y)
                       - u.unit_collision_radius - target_radius(target))
                if gap > MELEE_RELEASE_GAP:
                    continue
                self._damage(u.team, target, melee=u.Melee_attack)
                if u.kind == CATAPHRACT:
                    self._trample(u, target)
            else:
                self._spawn_projectile("arrow", u, target, u.Pierce_attack, 0,
                                       True, ARROW_SPEED, True)

    def _trample(self, cata, primary):
        """Section 72.4 : toutes les cibles ennemies dont le centre est à
        0.75 ou moins du centre du cataphracte subissent aussi le coup."""
        for o in list(self.grid.near(cata.x, cata.y, TRAMPLE_RADIUS + 0.1)):
            if o is primary or o.team == cata.team or not o.is_alive():
                continue
            d = math.hypot(o.x - cata.x, o.y - cata.y)
            if d <= TRAMPLE_RADIUS:
                self._damage(cata.team, o, melee=cata.Melee_attack)

    def _resolve_trebuchets(self, t):
        for u in self.units:
            if u.kind != TREBUCHET:
                continue
            shot = u.update(t, apply_damage=False)
            if shot is not None:
                bonus = (u.bonus_vs_buildings
                         if getattr(shot.target, "is_building", False) else 0)
                p = self._spawn_projectile("stone", u, shot.target, u.Pierce_attack,
                                           bonus, shot.hit, STONE_SPEED, False)
                p.tx, p.ty = shot.impact

    def _castle_fire(self, t):
        c = self.castle
        if c is None or not c.is_alive() or t + 1e-9 < c.next_attack_time:
            return
        best, best_d = None, math.inf
        for u in self.units:
            if u.team == c.team:
                continue
            d = (math.hypot(u.x - c.x, u.y - c.y) - c.footprint / 2.0
                 - u.unit_collision_radius)
            if d <= c.attack_range and d < best_d:
                best, best_d = u, d
        if best is None:
            return
        c.next_attack_time = t + c.reload_time
        for i in range(c.volley_size):
            p = self._spawn_projectile("arrow", c, best, c.attack, 0, True,
                                       ARROW_SPEED, True)
            # petites variations pour voir les 5 flèches
            p.x += (i - 2) * 0.25
            p.sx = p.x

    def _spawn_projectile(self, kind, src, target, pierce, bonus, hit, speed, homing):
        p = Projectile(kind, src.team, src.x, src.y, src.x, src.y,
                       target.x, target.y, target, speed, pierce, bonus, hit,
                       homing, self.time)
        self.projectiles.append(p)
        return p

    def _update_projectiles(self, t, dt):
        alive = []
        for p in self.projectiles:
            if p.homing and p.target.is_alive():
                p.tx, p.ty = p.target.x, p.target.y
            dx, dy = p.tx - p.x, p.ty - p.y
            d = math.hypot(dx, dy)
            step = p.speed * dt
            if d <= step:
                p.x, p.y = p.tx, p.ty
                if p.hit and p.target.is_alive():
                    self._damage(p.team, p.target, pierce=p.pierce, bonus=p.bonus)
                p.alive = False
            else:
                p.x += dx / d * step
                p.y += dy / d * step
                alive.append(p)
        self.projectiles = alive

    # ------------------------------------------------------------------
    # Comportement individuel
    # ------------------------------------------------------------------
    def _behave(self, u, t, dt):
        u.moving = False
        if u.kind == TREBUCHET:
            self._behave_trebuchet(u, t, dt)
            return
        if u.is_busy_attacking(t):
            return          # immobile pendant l'animation d'attaque
        order = u.order
        if order is None:
            return

        target = None
        if order.kind == "attack":
            target = order.target
            if target is None or not target.is_alive():
                u.order = None
                return
            if getattr(target, "is_building", False) and u.range <= 0:
                u.order = None   # falaise : pas d'attaque de mêlée sur le château
                return
        elif order.engage > 0:
            target = self._engage_target(u, order, t)

        if target is not None:
            if self.in_attack_range(u, target):
                if u.can_attack(t):
                    self._start_attack(u, target, t)
                return
            if order.kind == "attack" or u.range <= 0:
                self._move_unit(u, target.x, target.y, dt, chase=target)
                return

        if order.kind == "move":
            self._move_unit(u, order.x, order.y, dt)

    def _engage_target(self, u, order, t):
        cur = u.engaged
        if cur is not None and cur.is_alive() and t < u.next_scan:
            if self._engage_ok(u, order, cur):
                return cur
        u.next_scan = t + 0.4
        u.engaged = None
        radius = order.engage if u.range <= 0 else min(order.engage, u.range)
        best, best_key = None, None
        for e in self.grid.near(u.x, u.y, radius + 1.0):
            if e.team == u.team or not e.is_alive():
                continue
            if not self._engage_ok(u, order, e, radius):
                continue
            pref = order.prefer.index(e.kind) if e.kind in order.prefer else len(order.prefer)
            # un tireur vise d'abord ce qui n'est pas protégé par le Shield Wall
            covered = 1 if (u.range > 0 and getattr(e, "shield_wall", False)) else 0
            key = (pref, covered, math.hypot(e.x - u.x, e.y - u.y))
            if best_key is None or key < best_key:
                best, best_key = e, key
        u.engaged = best
        return best

    def _engage_ok(self, u, order, e, radius=None):
        if radius is None:
            radius = order.engage if u.range <= 0 else min(order.engage, u.range)
        if u.range > 0:
            if edge_distance(u, e) > radius:
                return False
        elif math.hypot(e.x - u.x, e.y - u.y) - e.unit_collision_radius > radius:
            return False
        if order.leash > 0 and math.hypot(e.x - order.x, e.y - order.y) > order.leash:
            return False
        return True

    def _behave_trebuchet(self, u, t, dt):
        order = u.order
        if order is None or u.is_busy_attacking(t):
            return
        if order.kind == "move":
            if u.is_unpacked():
                u.pack(t)
            elif u.is_packed():
                self._move_unit(u, order.x, order.y, dt)
            return
        target = order.target
        if target is None or not target.is_alive():
            u.order = None
            return
        if u.is_in_range(target):
            if u.is_packed():
                u.unpack(t)
            elif u.is_unpacked() and u.can_attack(t):
                if u.attack(target, t):
                    u.facing = math.atan2(target.y - u.y, target.x - u.x)
            return
        if u.is_unpacked():
            u.pack(t)
            return
        if u.is_packed():
            # se placer un peu en deçà de la portée max (ou s'éloigner si trop près)
            d = math.hypot(u.x - target.x, u.y - target.y)
            want = target_radius(target) + u.range - 0.8
            if d < 1e-6:
                return
            px = target.x + (u.x - target.x) / d * want
            py = target.y + (u.y - target.y) / d * want
            self._move_unit(u, px, py, dt)

    # ------------------------------------------------------------------
    # Déplacement et collisions (cercles, ni poussée ni inertie)
    # ------------------------------------------------------------------
    def _free(self, u, nx, ny):
        r = u.unit_collision_radius
        if not self.map.circle_is_free(nx, ny, r):
            return False
        for o in self.grid.near(nx, ny, r + 0.8):
            if o is u or not o.is_alive():
                continue
            rr = r + o.unit_collision_radius - 1e-6
            nd2 = (o.x - nx) ** 2 + (o.y - ny) ** 2
            if nd2 < rr * rr:
                # tolère de s'éloigner d'un chevauchement existant
                od2 = (o.x - u.x) ** 2 + (o.y - u.y) ** 2
                if nd2 <= od2:
                    return False
        return True

    def _move_unit(self, u, gx, gy, dt, chase=None):
        r = u.unit_collision_radius
        wx, wy = self.map.waypoint(u.x, u.y, gx, gy, r)
        dx, dy = wx - u.x, wy - u.y
        d = math.hypot(dx, dy)
        if d < 1e-3:
            return
        step = min(u.speed * dt, d)
        if chase is not None and (wx, wy) == (gx, gy):
            gap = d - r - target_radius(chase)
            step = min(step, max(0.0, gap))
            if step <= 1e-4:
                return
        ux, uy = dx / d, dy / d
        # près d'une simple destination on n'essaie que des petits écarts (pas
        # de tremblement autour de sa place) ; en poursuite on contourne toujours
        detours = _DETOURS_CS if (d > 0.6 or chase is not None) else _DETOURS_CS[:3]
        for ca, sa in detours:
            vx, vy = ux * ca - uy * sa, ux * sa + uy * ca
            nx, ny = u.x + vx * step, u.y + vy * step
            if self._free(u, nx, ny):
                u.x, u.y = nx, ny
                u.facing = math.atan2(vy, vx)
                u.moving = True
                return
        # bloqué : petits pas droit devant (pour se caler au contact exact)
        for frac in (0.5, 0.25, 0.1):
            nx, ny = u.x + ux * step * frac, u.y + uy * step * frac
            if self._free(u, nx, ny):
                u.x, u.y = nx, ny
                u.moving = True
                return
        if getattr(self, "_blocked", None) is not None:
            self._blocked.append((u, gx, gy, chase))

    # ------------------------------------------------------------------
    # Morts et fin de partie
    # ------------------------------------------------------------------
    def _remove_dead(self, t):
        alive = []
        for u in self.units:
            if u.is_alive():
                alive.append(u)
            else:
                u.death_time = t
                u.order = None
                self.losses.append((round(t, 2), u.uid, u.kind, u.team))
                self.corpses.append((u.x, u.y, u.kind, u.team, t))
        self.units = alive

    def _check_end(self, t):
        if self.castle is not None and not self.castle.is_alive():
            self._end(ROMAN, "château détruit")
        elif not any(u.kind == TREBUCHET for u in self.units):
            self._end(PARTHIAN, "tous les trébuchets sont détruits")
        elif not self.first_damage_done and t >= self.first_contact_timeout:
            self._end(None, f"timeout : aucun contact en {self.first_contact_timeout:.0f} s")
        elif self.first_damage_done and t - self.last_damage_time >= self.idle_timeout:
            self._end(None, f"timeout : aucun dégât pendant {self.idle_timeout:.0f} s")
        elif t >= self.max_time:
            self._end(None, "timeout : durée maximale atteinte")

    def _end(self, winner, reason):
        self.over = True
        self.winner = winner
        self.end_reason = reason
