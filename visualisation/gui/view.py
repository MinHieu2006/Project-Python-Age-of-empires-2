"""Visualisation 2.5D (isométrique) de la bataille, avec pygame.

Commandes :
    Espace           pause
    + / -            vitesse de la simulation (x0.25 à x32)
    flèches / ZQSD   déplacer la caméra (ou clic-glisser avec le bouton droit)
    molette          zoom
    clic minimap     centrer la caméra (on peut glisser)
    M                vue globale de la carte / retour
    F                afficher les formations (places + intention de l'IA)
    H                barres de vie
    L                journal des décisions des IA
    Échap            quitter
"""

import math

import pygame

from engine.constants import (
    CATAPHRACT, CAVALRY_ARCHER, LEGIONARY, PARTHIAN, ROMAN, TREBUCHET,
)
from visualisation.gui import sprites
from visualisation.gui.sprites import TEAM_COLOURS

TILE_W, TILE_H = 64, 32
SPEEDS = [0.25, 0.5, 1, 2, 4, 8, 16, 32]

GRASS = (92, 140, 64)
GRASS_DARK = (80, 124, 55)
GRID = (84, 128, 58)
CLIFF_TOP = (128, 104, 78)
CLIFF_LEFT = (96, 76, 56)
CLIFF_RIGHT = (78, 62, 46)
STONE_TOP = (176, 170, 160)
STONE_LEFT = (140, 134, 124)
STONE_RIGHT = (116, 110, 102)
BG = (18, 22, 18)
PANEL = (0, 0, 0, 150)
TEXT = (235, 235, 225)

TEAM_NAMES = {ROMAN: "Romains", PARTHIAN: "Parthes"}
KIND_SHORT = {LEGIONARY: "légionnaires", TREBUCHET: "trébuchets",
              CATAPHRACT: "cataphractes", CAVALRY_ARCHER: "archers à cheval"}


class BattleView:
    def __init__(self, world, screen, speed=1.0):
        self.world = world
        self.screen = screen
        self.speed_index = min(range(len(SPEEDS)), key=lambda i: abs(SPEEDS[i] - speed))
        self.paused = False
        self.zoom = 1.0
        self.saved_view = None
        self.show_formations = True
        self.show_health = True
        self.show_log = True
        self.dragging_minimap = False
        self.dragging_camera = None
        self.font = pygame.font.SysFont("dejavusans", 14)
        self.font_small = pygame.font.SysFont("dejavusans", 12)
        self.font_big = pygame.font.SysFont("dejavusans", 30, bold=True)
        # caméra centrée sur l'armée romaine
        romans = world.units_of(ROMAN)
        if romans:
            self.cam_x = sum(u.x for u in romans) / len(romans)
            self.cam_y = sum(u.y for u in romans) / len(romans)
        else:
            self.cam_x, self.cam_y = world.map.cx, world.map.cy
        self.decor = self._make_decor()

    @property
    def speed(self):
        return SPEEDS[self.speed_index]

    # ------------------------------------------------------------------
    # Projection isométrique
    # ------------------------------------------------------------------
    def to_screen(self, x, y):
        w, h = self.screen.get_size()
        dx, dy = x - self.cam_x, y - self.cam_y
        return (w / 2 + (dx - dy) * TILE_W / 2 * self.zoom,
                h / 2 + (dx + dy) * TILE_H / 2 * self.zoom)

    def to_world(self, sx, sy):
        w, h = self.screen.get_size()
        a = (sx - w / 2) / (TILE_W / 2 * self.zoom)     # dx - dy
        b = (sy - h / 2) / (TILE_H / 2 * self.zoom)     # dx + dy
        return self.cam_x + (a + b) / 2, self.cam_y + (b - a) / 2

    # ------------------------------------------------------------------
    # Minimap (coin bas droit)
    # ------------------------------------------------------------------
    def minimap_rect(self):
        w, h = self.screen.get_size()
        mw, mh = 260, 130
        return pygame.Rect(w - mw - 12, h - mh - 12, mw, mh)

    def mini_to_screen(self, x, y):
        r = self.minimap_rect()
        W, H = self.world.map.width, self.world.map.height
        return (r.x + r.w / 2 + (x / W - y / H) * r.w / 2,
                r.y + (x / W + y / H) * r.h / 2)

    def mini_to_world(self, mx, my):
        r = self.minimap_rect()
        W, H = self.world.map.width, self.world.map.height
        a = (mx - r.x - r.w / 2) / (r.w / 2)     # x/W - y/H
        b = (my - r.y) / (r.h / 2)               # x/W + y/H
        return (a + b) / 2 * W, (b - a) / 2 * H

    # ------------------------------------------------------------------
    # Événements
    # ------------------------------------------------------------------
    def handle_events(self, real_dt):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return False
                if ev.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif ev.key in (pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_EQUALS):
                    self.speed_index = min(self.speed_index + 1, len(SPEEDS) - 1)
                elif ev.key in (pygame.K_MINUS, pygame.K_KP_MINUS, pygame.K_6):
                    self.speed_index = max(self.speed_index - 1, 0)
                elif ev.key == pygame.K_m:
                    self.toggle_overview()
                elif ev.key == pygame.K_f:
                    self.show_formations = not self.show_formations
                elif ev.key == pygame.K_h:
                    self.show_health = not self.show_health
                elif ev.key == pygame.K_l:
                    self.show_log = not self.show_log
            elif ev.type == pygame.MOUSEWHEEL:
                self.zoom = max(0.12, min(3.0, self.zoom * (1.15 if ev.y > 0 else 1 / 1.15)))
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                if ev.button == 1 and self.minimap_rect().collidepoint(ev.pos):
                    self.dragging_minimap = True
                    self.cam_x, self.cam_y = self.mini_to_world(*ev.pos)
                elif ev.button == 3:
                    self.dragging_camera = ev.pos
            elif ev.type == pygame.MOUSEBUTTONUP:
                if ev.button == 1:
                    self.dragging_minimap = False
                elif ev.button == 3:
                    self.dragging_camera = None
            elif ev.type == pygame.MOUSEMOTION:
                if self.dragging_minimap:
                    self.cam_x, self.cam_y = self.mini_to_world(*ev.pos)
                elif self.dragging_camera is not None:
                    x0, y0 = self.to_world(*self.dragging_camera)
                    x1, y1 = self.to_world(*ev.pos)
                    self.cam_x += x0 - x1
                    self.cam_y += y0 - y1
                    self.dragging_camera = ev.pos

        keys = pygame.key.get_pressed()
        step = 25.0 * real_dt / self.zoom
        dx = dy = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_q] or keys[pygame.K_a]:
            dx, dy = dx - step, dy + step
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx, dy = dx + step, dy - step
        if keys[pygame.K_UP] or keys[pygame.K_z] or keys[pygame.K_w]:
            dx, dy = dx - step, dy - step
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dx, dy = dx + step, dy + step
        self.cam_x = min(max(self.cam_x + dx * 0.7, 0), self.world.map.width)
        self.cam_y = min(max(self.cam_y + dy * 0.7, 0), self.world.map.height)
        return True

    def toggle_overview(self):
        if self.saved_view is None:
            self.saved_view = (self.cam_x, self.cam_y, self.zoom)
            w, h = self.screen.get_size()
            W, H = self.world.map.width, self.world.map.height
            self.zoom = min(w / ((W + H) * TILE_W / 2), h / ((W + H) * TILE_H / 2)) * 0.95
            self.cam_x, self.cam_y = W / 2, H / 2
        else:
            self.cam_x, self.cam_y, self.zoom = self.saved_view
            self.saved_view = None

    # ------------------------------------------------------------------
    # Dessin
    # ------------------------------------------------------------------
    def _make_decor(self):
        """Quelques touffes d'herbe inoffensives (décor, sans collision)."""
        rng = self.world.rng.__class__(7)
        m = self.world.map
        out = []
        for _ in range(500):
            x, y = rng.uniform(0, m.width), rng.uniform(0, m.height)
            if m.circle_is_free(x, y, 1.0):
                out.append((x, y, rng.random()))
        return out

    def draw(self, alpha):
        scr = self.screen
        scr.fill(BG)
        self._draw_ground()
        self._draw_corpses()
        if self.show_formations:
            self._draw_formation_slots()
        self._draw_entities(alpha)
        self._draw_projectiles(alpha)
        if self.show_formations:
            self._draw_formation_labels()
        self._draw_hud()
        if self.show_log:
            self._draw_log()
        self._draw_minimap()
        if self.world.over:
            self._draw_banner()

    def _draw_ground(self):
        m = self.world.map
        corners = [self.to_screen(0, 0), self.to_screen(m.width, 0),
                   self.to_screen(m.width, m.height), self.to_screen(0, m.height)]
        pygame.draw.polygon(self.screen, GRASS, corners)
        if self.zoom > 0.3:
            for x, y, v in self.decor:
                sx, sy = self.to_screen(x, y)
                if -10 < sx < self.screen.get_width() + 10 and -10 < sy < self.screen.get_height() + 10:
                    pygame.draw.circle(self.screen, GRASS_DARK, (sx, sy), max(1, 3 * self.zoom * (0.5 + v)))
        step = 10
        for i in range(0, int(m.width) + 1, step):
            pygame.draw.line(self.screen, GRID, self.to_screen(i, 0), self.to_screen(i, m.height))
        for j in range(0, int(m.height) + 1, step):
            pygame.draw.line(self.screen, GRID, self.to_screen(0, j), self.to_screen(m.width, j))
        pygame.draw.polygon(self.screen, (50, 80, 40), corners, 2)

    def _iso_box(self, x0, y0, x1, y1, height, top, left, right):
        z = self.zoom
        h = height * z
        a = self.to_screen(x0, y0)
        b = self.to_screen(x1, y0)
        c = self.to_screen(x1, y1)
        d = self.to_screen(x0, y1)
        up = lambda p: (p[0], p[1] - h)
        pygame.draw.polygon(self.screen, left, [d, c, up(c), up(d)])
        pygame.draw.polygon(self.screen, right, [b, c, up(c), up(b)])
        pygame.draw.polygon(self.screen, top, [up(a), up(b), up(c), up(d)])

    def _draw_cliffs(self):
        for tx, ty in sorted(self.world.map.cliff_tiles(), key=lambda t: t[0] + t[1]):
            self._iso_box(tx, ty, tx + 1, ty + 1, 10, CLIFF_TOP, CLIFF_LEFT, CLIFF_RIGHT)

    def _draw_castle(self):
        c = self.world.castle
        if c is None:
            return
        img = sprites.castle_image()
        half = c.footprint / 2
        if img is not None:
            w = int(c.footprint * TILE_W * self.zoom)
            h = int(img.get_height() * w / img.get_width())
            img = pygame.transform.smoothscale(img, (w, h))
            sx, sy = self.to_screen(c.x + half, c.y + half)
            self.screen.blit(img, (sx - w / 2, sy - h))
        else:
            ruined = not c.is_alive()
            hgt = 18 if ruined else 46
            top, left, right = ((110, 105, 98), (90, 86, 80), (75, 72, 66)) if ruined else \
                (STONE_TOP, STONE_LEFT, STONE_RIGHT)
            self._iso_box(c.x - half, c.y - half, c.x + half, c.y + half, hgt, top, left, right)
            if not ruined:
                for ox, oy in ((-half, -half), (half - 1, -half), (-half, half - 1), (half - 1, half - 1)):
                    self._iso_box(c.x + ox, c.y + oy, c.x + ox + 1, c.y + oy + 1, 66,
                                  STONE_TOP, STONE_LEFT, STONE_RIGHT)
                sx, sy = self.to_screen(c.x, c.y)
                top_y = sy - 46 * self.zoom
                pygame.draw.line(self.screen, (60, 50, 40), (sx, top_y), (sx, top_y - 28 * self.zoom), 2)
                pygame.draw.polygon(self.screen, TEAM_COLOURS[PARTHIAN],
                                    [(sx, top_y - 28 * self.zoom), (sx + 18 * self.zoom, top_y - 22 * self.zoom),
                                     (sx, top_y - 16 * self.zoom)])
        # barre de vie du château
        sx, sy = self.to_screen(c.x - half, c.y - half)
        self._bar(sx, sy - 80 * self.zoom, 90 * self.zoom, c.HP / c.max_hp, PARTHIAN, 6)

    def _draw_corpses(self):
        t = self.world.time
        keep = []
        for x, y, kind, team, td in self.world.corpses:
            age = t - td
            if age > 40:
                continue
            keep.append((x, y, kind, team, td))
            sx, sy = self.to_screen(x, y)
            r = max(2, 9 * self.zoom * (1.6 if kind != LEGIONARY else 1.0))
            col = (70, 55, 40) if team == ROMAN else (50, 55, 75)
            pygame.draw.ellipse(self.screen, col, (sx - r, sy - r / 2, 2 * r, r))
        self.world.corpses = keep

    def _draw_formation_slots(self):
        for f in self.world.formations:
            if not f.members:
                continue
            col = TEAM_COLOURS.get(f.team, (255, 255, 255))
            light = tuple(min(255, v + 90) for v in col)
            if self.zoom > 0.35:
                for sx_, sy_ in f.slots_world:
                    sx, sy = self.to_screen(sx_, sy_)
                    pygame.draw.circle(self.screen, light, (sx, sy), max(1, 2 * self.zoom))
            target = f._target_point()
            if target is not None:
                a = self.to_screen(f.x, f.y)
                b = self.to_screen(*target)
                if math.hypot(b[0] - a[0], b[1] - a[1]) > 6:
                    pygame.draw.line(self.screen, light, a, b, 1)
                    pygame.draw.circle(self.screen, light, b, 4, 1)

    def _draw_formation_labels(self):
        for f in self.world.formations:
            if not f.members:
                continue
            col = TEAM_COLOURS.get(f.team, (255, 255, 255))
            dense = "serré" if f.is_dense() else "espacé"
            text = f"{f.name} · {f.shape} {dense}"
            if f.status:
                text += f" · {f.status}"
            sx, sy = self.to_screen(f.x, f.y)
            img = self.font_small.render(text, True, (255, 255, 255))
            bg = pygame.Surface((img.get_width() + 8, img.get_height() + 4), pygame.SRCALPHA)
            bg.fill((*col, 170))
            self.screen.blit(bg, (sx - bg.get_width() / 2, sy - 60 * self.zoom - 18))
            self.screen.blit(img, (sx - img.get_width() / 2, sy - 60 * self.zoom - 16))

    def _draw_entities(self, alpha):
        items = []
        for u in self.world.units:
            x = u.prev_x + (u.x - u.prev_x) * alpha
            y = u.prev_y + (u.y - u.prev_y) * alpha
            items.append((x + y, 1, u, x, y))
        c = self.world.castle
        items.append((self.world.map.cx * 2 - 3, 0, "cliffs", 0, 0))
        if c is not None:
            items.append((c.x + c.y + 2, 0, "castle", 0, 0))
        items.sort(key=lambda it: (it[0], it[1]))
        w, h = self.screen.get_size()
        t = self.world.time
        for _, _, u, x, y in items:
            if u == "cliffs":
                self._draw_cliffs()
                continue
            if u == "castle":
                self._draw_castle()
                continue
            sx, sy = self.to_screen(x, y)
            if sx < -80 or sx > w + 80 or sy < -100 or sy > h + 60:
                continue
            r = u.unit_collision_radius
            # ombre / cercle de collision au sol
            rx, ry = r * TILE_W / 2 * self.zoom * 1.41, r * TILE_H / 2 * self.zoom * 1.41
            pygame.draw.ellipse(self.screen, (40, 60, 30), (sx - rx, sy - ry, 2 * rx, 2 * ry))
            if u.kind == LEGIONARY and u.shield_wall:
                pygame.draw.ellipse(self.screen, (120, 200, 255),
                                    (sx - rx - 2, sy - ry - 1, 2 * rx + 4, 2 * ry + 2), 2)
            state = None
            if u.kind == TREBUCHET:
                state = "unpacked" if u.state in ("unpacked", "packing") else "packed"
            fx = math.cos(u.facing) - math.sin(u.facing)   # sens écran
            img = sprites.sprite(u.kind, u.team, self.zoom * 0.9, state, flip=fx < 0)
            self.screen.blit(img, (sx - img.get_width() / 2, sy - img.get_height() + 3 * self.zoom))
            if t - u.last_hit_time < 0.15:
                pygame.draw.circle(self.screen, (255, 230, 120), (sx, sy - img.get_height() / 2), 3)
            if self.show_health and u.HP < u.max_hp:
                self._bar(sx - 12 * self.zoom, sy - img.get_height() - 4, 24 * self.zoom,
                          u.HP / u.max_hp, u.team, 3)
            if u.kind == TREBUCHET and u.state in ("packing", "unpacking"):
                frac = 1 - max(0.0, u.state_change_end - t) / u.PACKING_TIME
                self._bar(sx - 20 * self.zoom, sy + 6, 40 * self.zoom, frac, None, 3)

    def _bar(self, x, y, width, frac, team, height):
        width = max(width, 10)
        pygame.draw.rect(self.screen, (30, 30, 30), (x, y, width, height))
        col = (90, 210, 90) if frac > 0.5 else (230, 190, 60) if frac > 0.25 else (220, 60, 50)
        if team is None:
            col = (230, 230, 120)
        pygame.draw.rect(self.screen, col, (x, y, width * max(0.0, min(1.0, frac)), height))

    def _draw_projectiles(self, alpha):
        z = self.zoom
        for p in self.world.projectiles:
            sx, sy = self.to_screen(p.x, p.y)
            if p.kind == "stone":
                arc = math.sin(math.pi * p.progress) * 90 * z
                pygame.draw.circle(self.screen, (40, 40, 40), (sx, sy), max(1, 3 * z))  # ombre
                pygame.draw.circle(self.screen, (120, 110, 95), (sx, sy - arc), max(2, 6 * z))
            else:
                tx, ty = self.to_screen(p.tx, p.ty)
                d = math.hypot(tx - sx, ty - sy) or 1
                ux, uy = (tx - sx) / d, (ty - sy) / d
                arc = math.sin(math.pi * p.progress) * 20 * z + 12 * z
                L = 10 * z
                col = (250, 240, 200) if p.team == PARTHIAN else (255, 200, 200)
                pygame.draw.line(self.screen, col, (sx - ux * L, sy - uy * L - arc), (sx, sy - arc), 2)

    def _text(self, text, x, y, font=None, col=TEXT):
        img = (font or self.font).render(text, True, col)
        self.screen.blit(img, (x, y))
        return img.get_height()

    def _panel(self, rect):
        s = pygame.Surface(rect.size, pygame.SRCALPHA)
        s.fill(PANEL)
        self.screen.blit(s, rect.topleft)

    def _draw_hud(self):
        w = self.world
        self._panel(pygame.Rect(8, 8, 340, 112))
        status = "PAUSE" if self.paused else f"x{self.speed:g}"
        y = 14
        y += self._text(f"Carrhae — {int(w.time // 60):02d}:{int(w.time % 60):02d}   [{status}]", 16, y)
        for team in (ROMAN, PARTHIAN):
            counts = {}
            for u in w.units_of(team):
                counts[u.kind] = counts.get(u.kind, 0) + 1
            txt = ", ".join(f"{n} {KIND_SHORT[k]}" for k, n in counts.items()) or "—"
            gen = w.generals.get(team, (None,))[0]
            name = gen.name if gen else "?"
            y += 2 + self._text(f"{TEAM_NAMES[team]} ({name}) : {txt}", 16, y + 2,
                                self.font_small, TEAM_COLOURS[team])
        if w.castle is not None:
            y += 4 + self._text(f"Château : {w.castle.HP} / {w.castle.max_hp} PV", 16, y + 4,
                                self.font_small)
        self._text("Espace pause · +/- vitesse · ZQSD/flèches · molette zoom · M carte · "
                   "F formations · H PV · L journal", 16, y + 6, self.font_small, (190, 190, 180))

    def _draw_log(self):
        lines = self.world.decision_log[-10:]
        if not lines:
            return
        width = 470
        x = self.screen.get_width() - width - 8
        self._panel(pygame.Rect(x, 8, width, 18 + 16 * len(lines)))
        y = 12
        y += self._text("Décisions des généraux", x + 8, y, self.font_small, (200, 200, 190))
        for t, team, name, text in lines:
            txt = f"{t:6.1f}s {name}: {text}"
            if len(txt) > 72:
                txt = txt[:71] + "…"
            col = tuple(min(255, v + 70) for v in TEAM_COLOURS[team])
            y += self._text(txt, x + 8, y + 2, self.font_small, col)

    def _draw_minimap(self):
        r = self.minimap_rect()
        self._panel(r.inflate(8, 8))
        W, H = self.world.map.width, self.world.map.height
        pts = [self.mini_to_screen(0, 0), self.mini_to_screen(W, 0),
               self.mini_to_screen(W, H), self.mini_to_screen(0, H)]
        pygame.draw.polygon(self.screen, (70, 110, 50), pts)
        c = self.world.castle
        if c is not None:
            col = (200, 200, 200) if c.is_alive() else (90, 90, 90)
            pygame.draw.circle(self.screen, col, self.mini_to_screen(c.x, c.y), 4)
        for u in self.world.units:
            col = TEAM_COLOURS[u.team]
            if u.kind == TREBUCHET:
                col = (255, 230, 80)
            pygame.draw.circle(self.screen, col, self.mini_to_screen(u.x, u.y),
                               3 if u.kind == TREBUCHET else 1.5)
        # zone visible
        sw, sh = self.screen.get_size()
        view = [self.to_world(0, 0), self.to_world(sw, 0), self.to_world(sw, sh), self.to_world(0, sh)]
        pygame.draw.polygon(self.screen, (255, 255, 255), [self.mini_to_screen(*p) for p in view], 1)
        pygame.draw.polygon(self.screen, (200, 200, 200), pts, 1)

    def _draw_banner(self):
        w = self.world
        if w.winner == ROMAN:
            text, col = "VICTOIRE ROMAINE", TEAM_COLOURS[ROMAN]
        elif w.winner == PARTHIAN:
            text, col = "VICTOIRE PARTHE", TEAM_COLOURS[PARTHIAN]
        else:
            text, col = "MATCH NUL", (200, 200, 200)
        sw, _ = self.screen.get_size()
        img = self.font_big.render(text, True, (255, 255, 255))
        sub = self.font.render(f"{w.end_reason} — {w.time:.0f} s — Échap pour quitter", True, TEXT)
        box = pygame.Rect(0, 0, max(img.get_width(), sub.get_width()) + 40, 80)
        box.center = (sw // 2, 150)
        pygame.draw.rect(self.screen, col, box, border_radius=8)
        self.screen.blit(img, (box.centerx - img.get_width() / 2, box.y + 10))
        self.screen.blit(sub, (box.centerx - sub.get_width() / 2, box.y + 50))


def run_view(world, speed=1.0, size=(1280, 760), max_frames=None, screenshot=None):
    pygame.init()
    screen = pygame.display.set_mode(size, pygame.RESIZABLE)
    pygame.display.set_caption("FormAItions — Carrhae")
    clock = pygame.time.Clock()
    view = BattleView(world, screen, speed)
    acc = 0.0
    frames = 0
    running = True
    while running:
        real_dt = clock.tick(60) / 1000.0
        running = view.handle_events(real_dt)
        if not view.paused and not world.over:
            acc += real_dt * view.speed
            n = 0
            while acc >= world.dt and n < 500:
                world.step()
                acc -= world.dt
                n += 1
            if n >= 500:
                acc = 0.0
        alpha = 1.0 if view.paused or world.over else max(0.0, min(1.0, acc / world.dt))
        view.draw(alpha)
        pygame.display.flip()
        frames += 1
        if max_frames is not None and frames >= max_frames:
            break
    if screenshot:
        pygame.image.save(screen, screenshot)
    pygame.quit()
    return view
