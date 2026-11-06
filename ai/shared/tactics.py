"""Outils géométriques communs aux généraux."""

import math


def unit_vector(ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    d = math.hypot(dx, dy)
    if d < 1e-9:
        return 0.0, 0.0, 0.0
    return dx / d, dy / d, d


def point_segment_distance(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    l2 = dx * dx + dy * dy
    if l2 < 1e-12:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / l2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def blockers_on_path(units, ax, ay, bx, by, width):
    """Nombre d'unités à moins de `width` du segment A-B."""
    return sum(1 for u in units
               if point_segment_distance(u.x, u.y, ax, ay, bx, by) < width)


def keep_out_of_castle(cmd, x, y, min_dist):
    """Repousse le point (x, y) hors du rayon `min_dist` autour du château."""
    c = cmd.castle
    if c is None or not c.is_alive():
        return x, y
    ux, uy, d = unit_vector(c.x, c.y, x, y)
    if d >= min_dist:
        return x, y
    if d < 1e-6:
        ux, uy = 1.0, 0.0
    return cmd.map.clamp(c.x + ux * min_dist, c.y + uy * min_dist, 1.0)


def clusters(units, link=1.0):
    """Regroupe les unités dont les centres sont à moins de `link`
    (composantes connexes)."""
    units = list(units)
    n = len(units)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    l2 = link * link
    for i in range(n):
        for j in range(i + 1, n):
            if (units[i].x - units[j].x) ** 2 + (units[i].y - units[j].y) ** 2 <= l2:
                parent[find(i)] = find(j)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(units[i])
    return list(groups.values())


class Announcer:
    """N'écrit dans le journal que les changements de décision."""

    def __init__(self):
        self._last = {}

    def say(self, cmd, key, text):
        if self._last.get(key) != text:
            self._last[key] = text
            cmd.log(text)
