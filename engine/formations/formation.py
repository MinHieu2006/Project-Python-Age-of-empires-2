"""Formations : contrôle au niveau du groupe (section 70 du sujet).

Une formation est un ensemble d'unités, une forme (des « places » définies
dans un repère local avant / côté), un point d'ancrage et une orientation.
À chaque pas, le moteur :
  1. retire les morts et recalcule les places pour les survivants
     (la formation se reforme d'elle-même après des pertes) ;
  2. avance l'ancrage vers son objectif, en ralentissant si les unités
     ont décroché (cohésion pendant la marche) ;
  3. attribue une place à chaque unité et lui donne l'ordre individuel
     d'y aller.

Ce qu'une IA peut exprimer :
  move_to, face_towards, set_shape (transition), spread / tighten,
  circle_around, follow, place_between (bloquer un passage),
  split, merge, detach (laisser une unité agir seule un moment).
"""

import math

from engine.world import Order

DENSE_SPACING = 0.405     # légionnaires au contact : Shield Wall (<= 0.42)
SPREAD_SPACING = 1.1      # rangs ouverts, rangées décalées
LOOSE_SPACING = 0.55      # écart pour se mettre en place avant de serrer les rangs

SHAPES = ("block", "line", "circle", "wedge")


def _row_gap(spacing):
    # Dense : maillage hexagonal (6 voisins à `spacing`).
    # Ouvert : rangées rapprochées et décalées pour qu'aucun cavalier
    # (diamètre 0.5) ne passe en diagonale.
    return spacing * math.sqrt(3) / 2 if spacing < 0.6 else spacing * 0.5


def local_slots(shape, n, spacing, ranks=None, radius=None):
    """Places dans le repère local (avant, côté), centrées sur (0, 0)."""
    if n <= 0:
        return []
    slots = []
    if shape in ("block", "line"):
        if ranks is None:
            ranks = 2 if shape == "line" else max(1, round(math.sqrt(n / 2.5)))
        ranks = max(1, min(ranks, n))
        cols = math.ceil(n / ranks)
        gap = _row_gap(spacing)
        remaining = n
        for k in range(ranks):
            count = min(cols, remaining)
            remaining -= count
            shift = (k % 2) * spacing / 2 if ranks > 1 else 0.0
            for i in range(count):
                lat = (i - (count - 1) / 2) * spacing + shift - (spacing / 4 if ranks > 1 else 0)
                fwd = -k * gap + (ranks - 1) * gap / 2
                slots.append((fwd, lat))
    elif shape == "circle":
        ranks = max(1, ranks or 1)
        gap = _row_gap(spacing)
        per_ring = math.ceil(n / ranks)
        base_r = max(radius or 0.0, per_ring * spacing / (2 * math.pi))
        remaining = n
        for k in range(ranks):
            count = min(per_ring, remaining)
            remaining -= count
            r = base_r + k * gap
            offset = (k % 2) * math.pi / max(count, 1)
            for i in range(count):
                a = offset + 2 * math.pi * i / count
                slots.append((r * math.cos(a), r * math.sin(a)))
    elif shape == "wedge":
        gap = _row_gap(spacing)
        k = 0
        while len(slots) < n:
            for i in range(k + 1):
                if len(slots) >= n:
                    break
                slots.append((-k * gap, (i - k / 2) * spacing))
            k += 1
        mean_f = sum(s[0] for s in slots) / len(slots)
        slots = [(f - mean_f, l) for f, l in slots]
    else:
        raise ValueError(f"forme inconnue : {shape}")
    return slots


class Formation:
    def __init__(self, world, units, shape="block", team=None, name="",
                 x=None, y=None, facing=0.0, spacing=DENSE_SPACING, ranks=None,
                 radius=None, engage=0.0, leash=1.5, prefer=()):
        self.world = world
        self.team = team
        self.name = name or shape
        self.shape = shape
        self.spacing = spacing
        self.ranks = ranks
        self.radius = radius
        self.engage = engage
        self.leash = leash
        self.prefer = tuple(prefer)
        self.members = []
        self.detached = {}            # unité -> fin du détachement
        self.facing = facing
        self.auto_facing = True
        self.goal = None
        self.follow_target = None
        self.follow_offset = (0.0, 0.0)
        self.speed_factor = 0.9            # l'ancrage avance un peu moins vite que les unités
        self.max_error = 1.0          # au-delà, l'ancrage attend les retardataires
        self.turn_rate = 0.8          # rad/s
        self.status = ""              # texte libre affiché (intention de l'IA)
        self._slot_of = {}
        self._tight = False           # formation dense : rangs serrés atteints ?
        self._swap_cooldown = {}
        self._dirty = True
        self._next_reassign = 0.0
        self.slots_world = []
        for u in units:
            self.add(u)
        c = self.centroid()
        self.x = x if x is not None else (c[0] if c else 0.0)
        self.y = y if y is not None else (c[1] if c else 0.0)

    # ------------------------------------------------------------------
    # Membres
    # ------------------------------------------------------------------
    @property
    def size(self):
        return len(self.members)

    def alive_members(self):
        return [u for u in self.members if u.is_alive()]

    def add(self, unit):
        if getattr(unit, "formation", None) is not None and unit.formation is not self:
            unit.formation.remove(unit)
        if unit not in self.members:
            self.members.append(unit)
        unit.formation = self
        self._dirty = True

    def remove(self, unit):
        if unit in self.members:
            self.members.remove(unit)
            self._dirty = True
        self.detached.pop(unit, None)
        if getattr(unit, "formation", None) is self:
            unit.formation = None

    def detach(self, unit, duration):
        """L'unité reste membre mais n'obéit plus à la formation pendant
        `duration` secondes (l'IA peut lui donner un ordre individuel)."""
        if unit in self.members:
            self.detached[unit] = self.world.time + duration

    def reattach(self, unit):
        self.detached.pop(unit, None)

    def is_detached(self, unit):
        return self.detached.get(unit, -1.0) > self.world.time

    def disband(self):
        for u in list(self.members):
            self.remove(u)
            u.order = None
        if self in self.world.formations:
            self.world.formations.remove(self)

    # ------------------------------------------------------------------
    # Ordres de groupe
    # ------------------------------------------------------------------
    def move_to(self, x, y, facing=None):
        self.follow_target = None
        self.goal = self.world.map.clamp(x, y, 1.0)
        if facing is not None:
            self.set_facing(facing)
        else:
            self.auto_facing = True

    def stop(self):
        self.goal = None
        self.follow_target = None

    def set_facing(self, angle):
        self.auto_facing = False
        self._target_facing = angle

    def face_towards(self, x, y):
        self.set_facing(math.atan2(y - self.y, x - self.x))

    def set_shape(self, shape, spacing=None, ranks=None, radius=None):
        """Transition vers une autre forme."""
        if shape not in SHAPES:
            raise ValueError(f"forme inconnue : {shape}")
        changed = (shape != self.shape or (spacing is not None and spacing != self.spacing)
                   or ranks != self.ranks or radius != self.radius)
        self.shape = shape
        if spacing is not None:
            self.spacing = spacing
        self.ranks = ranks
        self.radius = radius
        if changed:
            self._dirty = True

    def spread(self, spacing=SPREAD_SPACING, ranks=None):
        self.set_shape(self.shape, spacing=spacing, ranks=ranks if ranks else self.ranks,
                       radius=self.radius)

    def tighten(self, ranks=None):
        self.set_shape(self.shape, spacing=DENSE_SPACING, ranks=ranks if ranks else self.ranks,
                       radius=self.radius)

    def is_dense(self):
        return self.spacing < 0.6

    def circle_around(self, target, radius=None, ranks=None, spacing=None):
        """Former un cercle autour d'un point (x, y) ou d'une unité."""
        self.set_shape("circle", spacing=spacing if spacing else self.spacing,
                       ranks=ranks, radius=radius)
        if isinstance(target, tuple):
            self.move_to(*target)
        else:
            self.follow(target)

    def follow(self, target, offset=(0.0, 0.0)):
        """L'ancrage suit une unité, une formation ou un point (x, y)."""
        self.follow_target = target
        self.follow_offset = offset
        self.goal = None

    def place_between(self, protect, threat, distance):
        """Se placer entre `protect` et `threat`, à `distance` de `protect`,
        face à la menace (écran / blocage d'un passage)."""
        px, py = protect
        tx, ty = threat
        d = math.hypot(tx - px, ty - py)
        if d < 1e-6:
            return
        ux, uy = (tx - px) / d, (ty - py) / d
        dist = min(distance, d * 0.8)
        self.goal = self.world.map.clamp(px + ux * dist, py + uy * dist, 1.0)
        self.follow_target = None
        self.set_facing(math.atan2(uy, ux))

    def split(self, parts=2, names=None):
        """Coupe la formation en `parts` morceaux de gauche à droite.
        Renvoie la liste des formations (la première est `self`)."""
        units = self.alive_members()
        if parts < 2 or len(units) < parts:
            return [self]
        fx, fy = math.cos(self.facing), math.sin(self.facing)
        units.sort(key=lambda u: -(u.x - self.x) * fy + (u.y - self.y) * fx)
        size = math.ceil(len(units) / parts)
        groups = [units[i:i + size] for i in range(0, len(units), size)]
        result = [self]
        for i, g in enumerate(groups[1:], start=1):
            name = names[i] if names and i < len(names) else f"{self.name}-{i}"
            f = Formation(self.world, g, shape=self.shape, team=self.team, name=name,
                          facing=self.facing, spacing=self.spacing, ranks=self.ranks,
                          radius=self.radius, engage=self.engage, leash=self.leash,
                          prefer=self.prefer)
            self.world.formations.append(f)
            result.append(f)
        if names:
            self.name = names[0]
        self._dirty = True
        return result

    def merge(self, other):
        """Absorbe les membres de `other`, qui disparaît."""
        if other is self:
            return self
        for u in list(other.members):
            self.add(u)
        other.disband()
        return self

    # ------------------------------------------------------------------
    # Mesures
    # ------------------------------------------------------------------
    def centroid(self):
        units = self.alive_members()
        if not units:
            return None
        return (sum(u.x for u in units) / len(units), sum(u.y for u in units) / len(units))

    def _placed_ratio(self, tol=0.1):
        """Part des unités à moins de `tol` de leur place."""
        n = ok = 0
        for u in self.members:
            if self.is_detached(u):
                continue
            i = self._slot_of.get(u.uid)
            if i is None or i >= len(self.slots_world):
                continue
            n += 1
            sx, sy = self.slots_world[i]
            ok += math.hypot(u.x - sx, u.y - sy) < tol
        return ok / n if n else 0.0

    def cohesion(self):
        """Écart moyen entre les unités et leur place (0 = parfaite)."""
        errs = []
        for u in self.alive_members():
            if self.is_detached(u):
                continue
            i = self._slot_of.get(u.uid)
            if i is not None and i < len(self.slots_world):
                sx, sy = self.slots_world[i]
                errs.append(math.hypot(u.x - sx, u.y - sy))
        return sum(errs) / len(errs) if errs else 0.0

    def width(self):
        if len(self.slots_world) < 2:
            return 0.0
        fx, fy = math.cos(self.facing), math.sin(self.facing)
        lats = [-(sx - self.x) * fy + (sy - self.y) * fx for sx, sy in self.slots_world]
        return max(lats) - min(lats)

    # ------------------------------------------------------------------
    # Mise à jour par le moteur
    # ------------------------------------------------------------------
    def _target_point(self):
        t = self.follow_target
        if t is None:
            return self.goal
        if isinstance(t, tuple):
            return (t[0] + self.follow_offset[0], t[1] + self.follow_offset[1])
        if isinstance(t, Formation):
            # on suit les unités réelles de l'autre formation, pas son ancrage
            c = t.centroid() or (t.x, t.y)
            return (c[0] + self.follow_offset[0], c[1] + self.follow_offset[1])
        if not t.is_alive():
            self.follow_target = None
            return self.goal
        return (t.x + self.follow_offset[0], t.y + self.follow_offset[1])

    def update(self, t):
        before = len(self.members)
        self.members = [u for u in self.members if u.is_alive()]
        if len(self.members) != before:
            self._dirty = True        # pertes : on recalcule les places
        for u in list(self.detached):
            if not u.is_alive():
                del self.detached[u]
        if not self.members:
            return
        dt = self.world.dt

        # Ancrage : avance vers l'objectif au pas du plus lent
        target = self._target_point()
        if target is not None:
            dx, dy = target[0] - self.x, target[1] - self.y
            d = math.hypot(dx, dy)
            if d > 0.02:
                speed = min(u.speed for u in self.members) * self.speed_factor
                if self.cohesion() > self.max_error:
                    speed *= 0.2
                step = min(d, speed * dt)
                self.x += dx / d * step
                self.y += dy / d * step
                if self.auto_facing and d > 0.5:
                    self._target_facing = math.atan2(dy, dx)

        # Rotation progressive (évite de mélanger toutes les places)
        tf = getattr(self, "_target_facing", self.facing)
        diff = (tf - self.facing + math.pi) % (2 * math.pi) - math.pi
        max_turn = self.turn_rate * dt
        if abs(diff) > 1e-3:
            self.facing += max(-max_turn, min(max_turn, diff))

        # Une formation dense se met d'abord en place en ordre lâche, puis
        # serre les rangs : une unité ne peut pas se glisser entre deux
        # légionnaires déjà au contact.
        spacing = self.spacing
        if self.is_dense():
            err = self.cohesion()
            if self._tight and err > 0.8:
                self._tight = False
            elif not self._tight and self.slots_world and self._placed_ratio() >= 0.85:
                self._tight = True
            if not self._tight:
                spacing = LOOSE_SPACING

        # Places en coordonnées du monde
        active = [u for u in self.members if not self.is_detached(u)]
        local = local_slots(self.shape, len(active), spacing, self.ranks, self.radius)
        fx, fy = math.cos(self.facing), math.sin(self.facing)
        self.slots_world = [(self.x + f * fx - l * fy, self.y + f * fy + l * fx)
                            for f, l in local]

        if self._dirty or t >= self._next_reassign or len(self._slot_of) != len(active):
            self._assign(active)
            self._dirty = False
            self._next_reassign = t + 3.0
        self._unblock(active, spacing)

        for u in active:
            i = self._slot_of.get(u.uid)
            if i is None or i >= len(self.slots_world):
                continue
            sx, sy = self.world.map.clamp(*self.slots_world[i], margin=u.unit_collision_radius)
            o = u.order
            if (o is not None and o.kind == "move" and o.engage == self.engage
                    and o.leash == self.leash and o.prefer == self.prefer):
                o.x, o.y = sx, sy
            else:
                u.order = Order("move", sx, sy, engage=self.engage, leash=self.leash,
                                prefer=self.prefer)

    def _unblock(self, units, spacing):
        """Échange de places : une unité bloquée loin de sa place prend une
        place voisine plus proche d'elle ; l'occupant de cette place glisse
        vers la place libre. Le « trou » migre ainsi vers l'unité bloquée."""
        slots = self.slots_world
        if len(slots) < 2:
            return
        slot_of = self._slot_of
        now = self.world.time
        cooldown = self._swap_cooldown
        reach2 = (max(spacing, 0.45) * 2.2) ** 2
        for u in units:
            i = slot_of.get(u.uid)
            if i is None or i >= len(slots) or cooldown.get(u.uid, -1.0) > now:
                continue
            sx, sy = slots[i]
            err = math.hypot(u.x - sx, u.y - sy)
            if err < 0.25:
                continue
            best, best_d = None, err - 0.01
            for v in units:
                if v is u or cooldown.get(v.uid, -1.0) > now:
                    continue
                j = slot_of.get(v.uid)
                if j is None or j >= len(slots):
                    continue
                tx, ty = slots[j]
                if (tx - sx) ** 2 + (ty - sy) ** 2 > reach2:
                    continue
                d = math.hypot(u.x - tx, u.y - ty)
                if d < best_d:
                    best, best_d = v, d
            if best is not None:
                j = slot_of[best.uid]
                slot_of[u.uid], slot_of[best.uid] = j, i
                cooldown[u.uid] = cooldown[best.uid] = now + 2.0

    def _assign(self, units):
        """Attribution gloutonne unité -> place la plus proche."""
        pairs = []
        for ui, u in enumerate(units):
            for si, (sx, sy) in enumerate(self.slots_world):
                pairs.append(((u.x - sx) ** 2 + (u.y - sy) ** 2, ui, si))
        pairs.sort()
        used_u, used_s = set(), set()
        self._slot_of = {}
        for _, ui, si in pairs:
            if ui in used_u or si in used_s:
                continue
            used_u.add(ui)
            used_s.add(si)
            self._slot_of[units[ui].uid] = si
            if len(used_u) == len(units):
                break
