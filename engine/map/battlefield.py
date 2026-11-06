"""Géométrie du champ de bataille : plaine nue, château au centre entouré
d'un anneau de falaise d'une case (section 71.2)."""

import math

from engine.constants import CASTLE_FOOTPRINT, CLIFF_THICKNESS


class Battlefield:
    def __init__(self, width=120, height=120):
        self.width = float(width)
        self.height = float(height)
        self.cx = self.width / 2.0
        self.cy = self.height / 2.0
        half_castle = CASTLE_FOOTPRINT / 2.0
        # Emprise du château : [cx-2, cx+2]
        self.castle_half = half_castle
        # Château + falaise : carré infranchissable [cx-3, cx+3]
        self.block_half = half_castle + CLIFF_THICKNESS

    # ------------------------------------------------------------------
    # Tuiles (pour l'affichage)
    # ------------------------------------------------------------------
    def tile_kind(self, tx, ty):
        """'castle', 'cliff' ou 'plain' pour la tuile (tx, ty)."""
        dx = tx + 0.5 - self.cx
        dy = ty + 0.5 - self.cy
        if abs(dx) < self.castle_half and abs(dy) < self.castle_half:
            return "castle"
        if abs(dx) < self.block_half and abs(dy) < self.block_half:
            return "cliff"
        return "plain"

    def cliff_tiles(self):
        tiles = []
        lo = int(self.cx - self.block_half)
        hi = int(self.cx + self.block_half)
        for tx in range(lo, hi):
            for ty in range(lo, hi):
                if self.tile_kind(tx, ty) == "cliff":
                    tiles.append((tx, ty))
        return tiles

    # ------------------------------------------------------------------
    # Collisions avec le décor
    # ------------------------------------------------------------------
    def circle_is_free(self, x, y, r):
        """Vrai si un cercle de rayon r centré en (x, y) est dans la carte
        et ne touche ni la falaise ni le château."""
        if x - r < 0 or y - r < 0 or x + r > self.width or y + r > self.height:
            return False
        # Distance du centre au carré bloquant
        dx = max(abs(x - self.cx) - self.block_half, 0.0)
        dy = max(abs(y - self.cy) - self.block_half, 0.0)
        return dx * dx + dy * dy >= r * r

    def clamp(self, x, y, margin=0.5):
        return (min(max(x, margin), self.width - margin),
                min(max(y, margin), self.height - margin))

    # ------------------------------------------------------------------
    # « Pathfinding » : la seule entrave est le carré central. Si la ligne
    # droite le traverse, on passe par le coin le plus avantageux.
    # ------------------------------------------------------------------
    def _segment_hits_square(self, x0, y0, x1, y1, half):
        # Algorithme de Liang-Barsky sur le carré [c-half, c+half]
        xmin, xmax = self.cx - half, self.cx + half
        ymin, ymax = self.cy - half, self.cy + half
        dx, dy = x1 - x0, y1 - y0
        t0, t1 = 0.0, 1.0
        for p, q in ((-dx, x0 - xmin), (dx, xmax - x0),
                     (-dy, y0 - ymin), (dy, ymax - y0)):
            if p == 0:
                if q < 0:
                    return False
            else:
                t = q / p
                if p < 0:
                    if t > t1:
                        return False
                    t0 = max(t0, t)
                else:
                    if t < t0:
                        return False
                    t1 = min(t1, t)
        return t0 < t1

    def waypoint(self, x0, y0, x1, y1, r):
        """Point vers lequel se diriger pour aller de (x0,y0) à (x1,y1)."""
        half = self.block_half + r
        if not self._segment_hits_square(x0, y0, x1, y1, half - 0.01):
            return x1, y1
        corner_half = half + 0.35
        best, best_cost = None, math.inf
        for sx in (-1, 1):
            for sy in (-1, 1):
                kx = self.cx + sx * corner_half
                ky = self.cy + sy * corner_half
                visible = not self._segment_hits_square(x0, y0, kx, ky, half - 0.01)
                cost = math.hypot(kx - x0, ky - y0) + math.hypot(x1 - kx, y1 - ky)
                if not visible:
                    cost += 1000.0
                if cost < best_cost:
                    best, best_cost = (kx, ky), cost
        return best
