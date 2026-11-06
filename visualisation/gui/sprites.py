"""Sprites des unités.

Si un fichier `assets/sprites/<type>.png` existe (par exemple les sprites
d'Age of Empires II que le sujet recommande d'utiliser), il est chargé à la
place du dessin. Sinon un sprite simple est dessiné : silhouette lisible,
couleur du camp, échelle fidèle au cercle de collision.

Noms de fichiers reconnus : legionary.png, cataphract.png,
cavalry_archer.png, trebuchet_packed.png, trebuchet_unpacked.png,
castle.png (avec, en option, un suffixe _roman / _parthian)."""

import os

import pygame

from engine.constants import (
    CASTLE, CATAPHRACT, CAVALRY_ARCHER, LEGIONARY, PARTHIAN, ROMAN, TREBUCHET,
)

ASSET_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "sprites")

TEAM_COLOURS = {
    ROMAN: (200, 40, 40),
    PARTHIAN: (40, 95, 210),
}
TEAM_DARK = {
    ROMAN: (120, 20, 20),
    PARTHIAN: (20, 50, 130),
}

OUTLINE = (25, 20, 15)
SKIN = (222, 184, 140)
METAL = (170, 175, 185)
METAL_DARK = (110, 115, 125)
GOLD = (220, 180, 60)
WOOD = (130, 90, 50)
WOOD_DARK = (90, 60, 30)
HORSE = (120, 80, 50)
HORSE_LIGHT = (160, 115, 70)


# ----------------------------------------------------------------------
# Dessins de base (à l'échelle 1 : une case fait 64 px de large)
# ----------------------------------------------------------------------
def _legionary(team):
    s = pygame.Surface((26, 36), pygame.SRCALPHA)
    c, dk = TEAM_COLOURS[team], TEAM_DARK[team]
    pygame.draw.rect(s, SKIN, (11, 27, 3, 8))                        # jambes
    pygame.draw.rect(s, SKIN, (15, 27, 3, 8))
    pygame.draw.rect(s, c, (9, 13, 11, 15), border_radius=2)        # tunique
    pygame.draw.circle(s, SKIN, (14, 9), 5)                          # tête
    pygame.draw.arc(s, METAL, (8, 2, 12, 12), 0, 3.14, 4)            # casque
    pygame.draw.rect(s, c, (12, 0, 4, 4))                            # crête
    pygame.draw.rect(s, dk, (2, 12, 10, 18), border_radius=2)       # scutum
    pygame.draw.rect(s, OUTLINE, (2, 12, 10, 18), 1, border_radius=2)
    pygame.draw.circle(s, GOLD, (7, 21), 2)
    pygame.draw.line(s, METAL, (21, 6), (21, 28), 2)                 # pilum
    return s


def _horse(s, body, x0, y0, armoured):
    pygame.draw.ellipse(s, body, (x0, y0, 34, 14))                   # corps
    pygame.draw.polygon(s, body, [(x0 + 28, y0 + 4), (x0 + 38, y0 - 8),
                                  (x0 + 43, y0 - 5), (x0 + 34, y0 + 8)])  # cou + tête
    for lx in (x0 + 4, x0 + 9, x0 + 24, x0 + 29):
        pygame.draw.line(s, body, (lx, y0 + 10), (lx, y0 + 22), 3)   # pattes
    if armoured:
        for i in range(5):
            pygame.draw.arc(s, METAL_DARK, (x0 + 2 + i * 6, y0 + 1, 8, 10), 3.14, 6.28, 2)
    pygame.draw.ellipse(s, OUTLINE, (x0, y0, 34, 14), 1)


def _cataphract(team):
    s = pygame.Surface((48, 46), pygame.SRCALPHA)
    _horse(s, METAL, 2, 22, True)
    c = TEAM_COLOURS[team]
    pygame.draw.rect(s, c, (15, 10, 10, 14), border_radius=2)        # cavalier
    pygame.draw.circle(s, METAL, (20, 7), 5)                         # casque
    pygame.draw.line(s, METAL_DARK, (8, 20), (46, 2), 2)             # lance
    pygame.draw.rect(s, TEAM_DARK[team], (6, 26, 26, 4))             # caparaçon
    return s


def _cavalry_archer(team):
    s = pygame.Surface((48, 46), pygame.SRCALPHA)
    _horse(s, HORSE_LIGHT, 2, 22, False)
    c = TEAM_COLOURS[team]
    pygame.draw.rect(s, c, (15, 10, 9, 14), border_radius=2)
    pygame.draw.circle(s, SKIN, (19, 7), 4)
    pygame.draw.polygon(s, TEAM_DARK[team], [(15, 4), (23, 4), (19, -1)])  # bonnet
    pygame.draw.arc(s, WOOD_DARK, (24, 4, 10, 20), -1.4, 1.4, 2)     # arc
    pygame.draw.line(s, (230, 230, 230), (27, 5), (27, 23), 1)       # corde
    return s


def _trebuchet(team, unpacked):
    c = TEAM_COLOURS[team]
    if not unpacked:
        s = pygame.Surface((72, 40), pygame.SRCALPHA)
        pygame.draw.rect(s, WOOD, (6, 18, 60, 10))                   # chariot
        pygame.draw.rect(s, OUTLINE, (6, 18, 60, 10), 1)
        pygame.draw.line(s, WOOD_DARK, (4, 14), (68, 10), 5)         # bras couché
        for wx in (14, 56):
            pygame.draw.circle(s, WOOD_DARK, (wx, 31), 7)
            pygame.draw.circle(s, OUTLINE, (wx, 31), 7, 1)
        pygame.draw.rect(s, c, (30, 8, 10, 6))
        return s
    s = pygame.Surface((70, 86), pygame.SRCALPHA)
    pygame.draw.rect(s, WOOD, (6, 72, 58, 9))                        # base
    pygame.draw.polygon(s, WOOD_DARK, [(14, 74), (33, 30), (37, 30), (22, 74)], 0)
    pygame.draw.polygon(s, WOOD_DARK, [(56, 74), (37, 30), (33, 30), (48, 74)], 0)
    pygame.draw.line(s, WOOD, (35, 32), (8, 4), 5)                   # bras levé
    pygame.draw.line(s, WOOD, (35, 32), (52, 46), 5)
    pygame.draw.rect(s, (90, 90, 95), (46, 44, 14, 14))              # contrepoids
    pygame.draw.rect(s, OUTLINE, (46, 44, 14, 14), 1)
    pygame.draw.rect(s, c, (28, 60, 14, 8))
    return s


_BASE = {}
_SCALED = {}


def _load_file(kind, team, state=None):
    names = []
    base = kind if state is None else f"{kind}_{state}"
    names.append(f"{base}_{team.lower()}.png")
    names.append(f"{base}.png")
    for n in names:
        path = os.path.join(ASSET_DIR, n)
        if os.path.exists(path):
            try:
                return pygame.image.load(path).convert_alpha()
            except pygame.error:
                return None
    return None


def base_sprite(kind, team, state=None):
    key = (kind, team, state)
    if key not in _BASE:
        surf = _load_file(kind, team, state)
        if surf is None:
            if kind == LEGIONARY:
                surf = _legionary(team)
            elif kind == CATAPHRACT:
                surf = _cataphract(team)
            elif kind == CAVALRY_ARCHER:
                surf = _cavalry_archer(team)
            elif kind == TREBUCHET:
                surf = _trebuchet(team, state == "unpacked")
            else:
                surf = pygame.Surface((8, 8), pygame.SRCALPHA)
        _BASE[key] = surf
    return _BASE[key]


def sprite(kind, team, zoom, state=None, flip=False):
    z = round(zoom, 2)
    key = (kind, team, state, z, flip)
    surf = _SCALED.get(key)
    if surf is None:
        b = base_sprite(kind, team, state)
        w = max(2, int(b.get_width() * z))
        h = max(2, int(b.get_height() * z))
        surf = pygame.transform.smoothscale(b, (w, h))
        if flip:
            surf = pygame.transform.flip(surf, True, False)
        if len(_SCALED) > 600:
            _SCALED.clear()
        _SCALED[key] = surf
    return surf


def castle_image():
    return _load_file(CASTLE, PARTHIAN)
