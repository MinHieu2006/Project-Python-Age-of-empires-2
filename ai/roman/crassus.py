"""CRASSUS : général romain conscient des formations.

Idée générale (section 74 du sujet) :
  * les trébuchets avancent en bloc vers une position de tir choisie à la
    portée maximale, hors de portée du château, du côté romain ;
  * une ESCORTE colle aux trébuchets. Tant que les cataphractes sont loin,
    c'est une ligne serrée en Shield Wall, derrière eux (les flèches ne font
    qu'1 dégât) ; dès qu'ils approchent, elle se transforme en ANNEAU autour
    des trébuchets, assez serré (écart < 0.5) pour qu'aucun cavalier ne passe ;
  * un ÉCRAN se place entre les trébuchets et les cataphractes : serré en
    Shield Wall tant que les flèches sont la menace, ouvert sur deux rangs
    décalés dès que les cataphractes approchent (moins de piétinement, plus
    de largeur, toujours infranchissable) ;
  * des groupes de TIRAILLEURS en Shield Wall repoussent les archers à
    cheval qui s'approchent des trébuchets, sans dépasser une laisse : ils
    protègent l'espace en menaçant de le bloquer ;
  * RIPOSTE : un cataphracte au contact est encerclé à 3 contre 1 ;
  * personne ne s'aventure à portée du château, pas même le bout d'une ligne.

Densité : une formation « dense » est une ligne de deux rangs décalés au
contact (0.405). Chaque légionnaire, sauf aux extrémités, y a exactement 4
voisins : c'est la forme qui met le plus d'hommes en Shield Wall (un bloc
carré a trop d'hommes au bord). Une telle ligne garde le Shield Wall en
marche, mais le perd dès qu'elle pivote (les extrémités décrochent) : on ne
réoriente donc une formation dense que si la menace a nettement tourné.

Paramètres :
  aggressiveness (0-100) : longueur de la laisse des tirailleurs et
      distance de poursuite des archers ;
  screen_distance : distance de l'écran devant les trébuchets ;
  cata_alert : distance des cataphractes à laquelle les groupes s'ouvrent ;
  ring_alert : distance des cataphractes aux trébuchets à laquelle
      l'escorte passe de la ligne à l'anneau ;
  skirmish_groups / skirmish_size : groupes de tirailleurs ;
  march_speed : fraction de la vitesse des trébuchets pendant la marche ;
  chase : les tirailleurs poursuivent-ils les archers (False : simple garde) ;
  melee_reach : distance max à laquelle un légionnaire va riposter.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Optional, Sequence

from ai.shared.general import General
from ai.shared.tactics import Announcer, keep_out_of_castle, unit_vector
from engine.constants import CATAPHRACT, CAVALRY_ARCHER, LEGIONARY, TREBUCHET
from engine.formations.formation import DENSE_SPACING

if TYPE_CHECKING:
    from engine.command import Commander
    from engine.formations.formation import Formation
    from engine.units.base_unit import BaseUnit

Point = tuple[float, float]

LEGIONARY_RADIUS: float = 0.2
SPREAD: float = 1.0                  # écart des rangs ouverts
RING_GAP: float = 0.82               # écart max dans l'anneau (catas : 0.5 de diamètre)
FIRE_MARGIN: float = 0.8             # marge sous la portée max des trébuchets
CASTLE_MARGIN: float = 1.3           # marge hors de la portée du château
CONTACT: float = 1.0                 # distance (centres) d'un cataphracte « au contact »
REFACE_ANGLE: float = math.radians(35)   # rotation minimale d'une formation dense
DENSE_RANKS: int = 2


def angle_diff(a: float, b: float) -> float:
    """Écart absolu entre deux angles, dans [0, pi]."""
    return abs((a - b + math.pi) % (2 * math.pi) - math.pi)


class Crassus(General):
    name = "CRASSUS"

    def __init__(self, aggressiveness: float = 50, screen_distance: float = 3.5,
                 cata_alert: float = 8.0, ring_alert: float = 12.0,
                 skirmish_groups: int = 2, skirmish_size: int = 8,
                 march_speed: float = 0.9, chase: bool = True,
                 melee_reach: float = 2.5) -> None:
        super().__init__(aggressiveness=aggressiveness, screen_distance=screen_distance,
                         cata_alert=cata_alert, ring_alert=ring_alert,
                         skirmish_groups=skirmish_groups, skirmish_size=skirmish_size,
                         march_speed=march_speed, chase=chase,
                         melee_reach=melee_reach)
        self.aggressiveness: float = aggressiveness
        self.screen_distance: float = screen_distance
        self.cata_alert: float = cata_alert
        self.ring_alert: float = ring_alert
        self.n_skirmish: int = skirmish_groups
        self.skirmish_size: int = skirmish_size
        self.march_speed: float = march_speed
        self.chase: bool = chase
        self.melee_reach: float = melee_reach
        self.ann: Announcer = Announcer()
        self.firing_point: Optional[Point] = None
        self.toward_castle: float = 0.0
        self.castle_safe: float = 0.0
        self.cluster_r: float = 0.0
        self.ring_r: float = 0.0
        self.escort_target: int = 0
        self.siege: bool = False
        self.formed: bool = False
        self.halt_since: Optional[float] = None
        self.escort_ring: bool = False
        self.trebs: Formation
        self.escort: Formation
        self.screen: Optional[Formation] = None
        self.skirmishers: list[Formation] = []
        self.skirmish_side: dict[Formation, int] = {}   # flanc : +1 / -1

    # ------------------------------------------------------------------
    def setup(self, cmd: Commander) -> None:
        trebs = cmd.my_units(TREBUCHET)
        legs = cmd.my_units(LEGIONARY)
        c = cmd.castle
        rx, ry = cmd.centroid(cmd.my_units())
        ux, uy, _ = unit_vector(c.x, c.y, rx, ry)
        # Portée max des trébuchets (mesurée au bord du château), moins une marge
        fire_d = c.footprint / 2 + (trebs[0].range if trebs else 16.0) - FIRE_MARGIN
        self.firing_point = (c.x + ux * fire_d, c.y + uy * fire_d)
        self.toward_castle = math.atan2(-uy, -ux)
        # Aucun légionnaire à portée du château (portée mesurée bord à bord)
        self.castle_safe = (c.footprint / 2 + c.attack_range + LEGIONARY_RADIUS
                            + CASTLE_MARGIN)

        # Trébuchets : petit bloc compact
        self.trebs = cmd.formation(trebs, shape="wedge", name="Trébuchets", spacing=1.5)
        self.trebs.move_to(*self.firing_point, facing=self.toward_castle)
        self.trebs.max_error = 1.5
        self.trebs.speed_factor = self.march_speed

        # Répartition des légionnaires
        legs = sorted(legs, key=lambda u: math.hypot(u.x - rx, u.y - ry))
        cluster_r = 0.8 * math.sqrt(max(len(trebs), 1)) + 0.5
        ring_r = cluster_r + 0.9
        n_ring = min(len(legs), math.ceil(2 * math.pi * ring_r / RING_GAP))
        ring = legs[:n_ring]
        rest = legs[n_ring:]
        groups: list[list[BaseUnit]] = []
        for _ in range(self.n_skirmish):
            if len(rest) >= self.skirmish_size + 8:
                groups.append(rest[:self.skirmish_size])
                rest = rest[self.skirmish_size:]
        screen = rest

        self.cluster_r = cluster_r
        self.ring_r = ring_r
        self.escort_target = len(ring)
        self.escort = cmd.formation(ring, shape="line", name="Escorte",
                                    spacing=DENSE_SPACING, ranks=DENSE_RANKS,
                                    engage=0.12, leash=0.5, prefer=(CATAPHRACT,))
        self._escort_line()
        if screen:
            self.screen = cmd.formation(screen, shape="line", name="Écran",
                                        ranks=DENSE_RANKS,
                                        spacing=DENSE_SPACING, engage=1.0, leash=1.6,
                                        prefer=(CATAPHRACT,))
        for i, g in enumerate(groups):
            f = cmd.formation(g, shape="line", name=f"Tirailleurs {i + 1}",
                              ranks=DENSE_RANKS, spacing=DENSE_SPACING,
                              engage=1.0, leash=2.5, prefer=(CAVALRY_ARCHER,))
            self.skirmish_side[f] = 1 if i % 2 == 0 else -1
            self.skirmishers.append(f)
        cmd.log(f"Plan : {len(trebs)} trébuchets vers ({self.firing_point[0]:.0f}, "
                f"{self.firing_point[1]:.0f}) à {fire_d:.1f} du château, escorte "
                f"{len(ring)}, écran {len(screen)}, {len(groups)} groupes de tirailleurs")

    # ------------------------------------------------------------------
    def decide(self, cmd: Commander) -> None:
        trebs = cmd.my_units(TREBUCHET)
        if not trebs:
            return
        tx, ty = cmd.centroid(trebs)
        catas = cmd.enemy_units(CATAPHRACT)
        hcas = cmd.enemy_units(CAVALRY_ARCHER)
        near_cata, d_cata = cmd.nearest(tx, ty, catas)

        self._escort(cmd, d_cata)
        self._trebuchets(cmd, trebs, near_cata, d_cata)
        self._screen(cmd, tx, ty, catas, near_cata, d_cata)
        self._skirmish(cmd, tx, ty, hcas, catas)
        self._gang_up(cmd, tx, ty, catas)

    # ------------------------------------------------------------------
    # Densité et orientation
    # ------------------------------------------------------------------
    @staticmethod
    def _make_dense(f: Formation) -> None:
        """Ligne serrée de deux rangs en Shield Wall (contre les flèches)."""
        f.set_shape("line", spacing=DENSE_SPACING, ranks=DENSE_RANKS)

    @staticmethod
    def _make_open(f: Formation) -> None:
        """Ligne ouverte sur deux rangs décalés (contre le piétinement)."""
        f.set_shape("line", spacing=SPREAD, ranks=2)

    @staticmethod
    def _face(f: Formation, angle: float) -> None:
        """Oriente la formation vers `angle`, mais une formation dense ne
        pivote que si l'écart dépasse REFACE_ANGLE (pivoter la disloque)."""
        current: float = getattr(f, "_target_facing", f.facing)
        if not f.is_dense() or angle_diff(angle, current) > REFACE_ANGLE:
            f.set_facing(angle)
        else:
            f.auto_facing = False

    def _safe(self, cmd: Commander, x: float, y: float, extra: float = 0.0) -> Point:
        return keep_out_of_castle(cmd, x, y, self.castle_safe + extra)

    def _keep_out(self, cmd: Commander, f: Formation, gx: float, gy: float) -> Point:
        """Repousse l'objectif (gx, gy) de la formation `f` jusqu'à ce
        qu'aucune de ses places ne soit à portée du château. Une ligne
        ouverte fait 11 cases de large : tenir son centre hors de portée ne
        suffit pas quand elle est orientée vers le château."""
        c = cmd.castle
        gx, gy = self._safe(cmd, gx, gy)
        if c is None or not c.is_alive() or not f.slots_world:
            return gx, gy
        offsets = [(sx - f.x, sy - f.y) for sx, sy in f.slots_world]
        for _ in range(3):
            worst = max(self.castle_safe - math.hypot(gx + ox - c.x, gy + oy - c.y)
                        for ox, oy in offsets)
            if worst <= 0:
                break
            ux, uy, d = unit_vector(c.x, c.y, gx, gy)
            if d < 1e-6:
                ux, uy = 1.0, 0.0
            gx, gy = cmd.map.clamp(gx + ux * (worst + 0.1), gy + uy * (worst + 0.1), 1.0)
        return gx, gy

    # ------------------------------------------------------------------
    # Escorte : ligne en Shield Wall ou anneau infranchissable
    # ------------------------------------------------------------------
    def _escort_line(self) -> None:
        """Ligne serrée collée aux trébuchets, du côté opposé au château
        (l'écran, lui, est devant)."""
        e = self.escort
        if not e.size:
            return
        self._make_dense(e)
        back = self.toward_castle + math.pi
        dist = self.cluster_r + 0.6 + DENSE_SPACING / 2
        e.follow(self.trebs, offset=(dist * math.cos(back), dist * math.sin(back)))
        e.set_facing(back)

    def _escort(self, cmd: Commander, d_cata: float) -> None:
        e = self.escort
        # Pertes : on prélève des légionnaires sur l'écran pour garder l'effectif
        if (e.size < self.escort_target and self.screen is not None
                and self.screen.size > 8):
            donor, _ = cmd.nearest(e.x, e.y, self.screen.alive_members())
            if donor is not None:
                e.add(donor)
                self.ann.say(cmd, "esc", "Escorte : un légionnaire de l'écran comble un trou")
        if not e.size:
            return

        # Transition ligne <-> anneau selon la distance des cataphractes (hystérésis)
        if not self.escort_ring and d_cata < self.ring_alert:
            self.escort_ring = True
            e.follow(self.trebs)
            self.ann.say(cmd, "esc-mode",
                         f"Escorte : ANNEAU autour des trébuchets (cataphractes à {d_cata:.0f})")
        elif self.escort_ring and d_cata > self.ring_alert + 4.0:
            self.escort_ring = False
            self._escort_line()
            self.ann.say(cmd, "esc-mode", "Escorte : LIGNE en Shield Wall (plus de cataphractes)")

        if not self.escort_ring:
            e.status = "SHIELD WALL"
            return
        # Tant qu'un trébuchet n'est pas dans l'anneau, il s'élargit pour le
        # laisser entrer ; ensuite il se resserre (infranchissable)
        cx, cy = e.centroid() or (e.x, e.y)
        outside = any(math.hypot(t.x - cx, t.y - cy) > self.ring_r - 0.4
                      for t in self.trebs.alive_members())
        loose = outside and d_cata > 10.0 and not self.siege
        r = self.ring_r + (2.5 if loose else 0.0)
        if e.shape != "circle" or abs((e.radius or 0) - r) > 1e-6:
            e.set_shape("circle", spacing=2 * math.pi * r / e.size, radius=r)
        e.status = "ANNEAU OUVERT" if loose else "ANNEAU FERMÉ"

    # ------------------------------------------------------------------
    # Trébuchets
    # ------------------------------------------------------------------
    def _trebuchets(self, cmd: Commander, trebs: Sequence[BaseUnit],
                    near_cata: Optional[BaseUnit], d_cata: float) -> None:
        assert self.firing_point is not None
        fx, fy = self.firing_point
        tf = self.trebs
        at_spot = math.hypot(tf.x - fx, tf.y - fy) < 0.5
        if not self.siege and at_spot:
            self.siege = True
            for t in trebs:
                tf.detach(t, 1e9)
                cmd.attack(t, cmd.castle)
            self.ann.say(cmd, "treb", "Trébuchets en batterie : déploiement et tir sur le château")
            return
        if self.siege:
            for t in trebs:
                if t.order is None:
                    cmd.attack(t, cmd.castle)
            return
        # Rassemblement : on ne part pas avant que l'escorte soit en place
        if not self.formed:
            ready = self.trebs.cohesion() < 0.8 and self.escort.cohesion() < 0.8
            if self.escort.size == 0 or (ready and cmd.time > 3) or cmd.time > 25:
                self.formed = True
            else:
                tf.speed_factor = 0.0
                self.ann.say(cmd, "treb", "Rassemblement : l'escorte se met en place")
                return
        # Cataphractes tout près : halte le temps que l'anneau se ferme
        # (un anneau immobile est étanche, un anneau en marche l'est moins).
        # Halte courte : chaque seconde de marche se paie en flèches.
        if near_cata is not None and d_cata < 7.0:
            if self.halt_since is None:
                self.halt_since = cmd.time
            if cmd.time - self.halt_since < 12.0 and self.escort.cohesion() > 0.3:
                tf.speed_factor = 0.0
                self.ann.say(cmd, "treb", "Trébuchets : halte, anneau fermé face aux cataphractes")
                return
        elif d_cata > 11.0:
            self.halt_since = None
        # Marche : l'escorte doit suivre, sinon on ralentit
        if self.escort.size and self.escort.cohesion() > 0.8:
            tf.speed_factor = 0.4
            self.ann.say(cmd, "treb", "Trébuchets : on attend que l'escorte se reforme")
        else:
            tf.speed_factor = self.march_speed
            self.ann.say(cmd, "treb", "Trébuchets : en marche vers la position de tir")

    # ------------------------------------------------------------------
    # Écran
    # ------------------------------------------------------------------
    def _screen(self, cmd: Commander, tx: float, ty: float, catas: Sequence[BaseUnit],
                near_cata: Optional[BaseUnit], d_cata: float) -> None:
        s = self.screen
        if s is None or not s.size:
            return
        if catas:
            thx, thy = cmd.centroid(catas)
        else:
            thx, thy = cmd.castle.x, cmd.castle.y

        # Cataphractes déjà près des trébuchets : l'écran se rabat dessus
        if near_cata is not None and d_cata < 3.5:
            s.place_between((tx, ty), (near_cata.x, near_cata.y), 1.5)
            s.goal = self._keep_out(cmd, s, *s.goal)
            if s.is_dense():
                self._make_open(s)
            s.status = "REPLI"
            self.ann.say(cmd, "screen", "Écran : repli pour couvrir les trébuchets")
            return

        # Entre les trébuchets et la menace, mais une ligne dense ne pivote pas
        # à chaque mouvement de l'ennemi : elle garde son axe tant que la
        # menace reste dans un cône de REFACE_ANGLE.
        threat_ang = math.atan2(thy - ty, thx - tx)
        self._face(s, threat_ang)
        ang: float = getattr(s, "_target_facing", threat_ang)
        dist = min(self.screen_distance, 0.8 * math.hypot(thx - tx, thy - ty))
        gx, gy = tx + math.cos(ang) * dist, ty + math.sin(ang) * dist
        s.goal = self._keep_out(cmd, s, *cmd.map.clamp(gx, gy, 1.0))
        s.follow_target = None

        sx, sy = s.centroid() or (s.x, s.y)
        _, d_screen = cmd.nearest(sx, sy, catas)
        if s.is_dense() and d_screen < self.cata_alert:
            self._make_open(s)
            self.ann.say(cmd, "screen", f"Écran : OUVERT (cataphractes à {d_screen:.1f})")
        elif not s.is_dense() and d_screen > self.cata_alert + 2.5:
            self._make_dense(s)
            self.ann.say(cmd, "screen", "Écran : SHIELD WALL (flèches)")
        s.status = "DENSE" if s.is_dense() else "OUVERT"

    # ------------------------------------------------------------------
    # Riposte en mêlée
    # ------------------------------------------------------------------
    def _gang_up(self, cmd: Commander, tx: float, ty: float,
                 catas: Sequence[BaseUnit]) -> None:
        """Riposte : un cataphracte près des trébuchets, ou au contact de
        n'importe quel légionnaire, est encerclé par les 3 légionnaires les
        plus proches. Sans cela, les légionnaires qui regagnent leur place
        dans la formation se font piétiner sans rendre les coups.
        L'escorte en anneau ne riposte qu'avec les hommes déjà au contact
        (l'anneau ne doit pas se vider), sauf si l'ennemi est à l'intérieur."""
        free: list[BaseUnit] = []
        for f in [self.screen, *self.skirmishers]:
            if f is not None:
                free.extend(f.alive_members())
        escort = self.escort.alive_members()
        ex, ey = self.escort.centroid() or (tx, ty)
        inside = [c for c in catas if math.hypot(c.x - ex, c.y - ey) < self.ring_r - 0.3]
        ring_holds = self.escort_ring and not inside
        if not ring_holds:
            free.extend(escort)
        taken: set[BaseUnit] = set()
        engaged = 0
        for c in sorted(catas, key=lambda c: math.hypot(c.x - tx, c.y - ty)):
            pool = free if not ring_holds else free + [
                u for u in escort if math.hypot(u.x - c.x, u.y - c.y) < CONTACT]
            near = sorted((u for u in pool if u not in taken
                           and math.hypot(u.x - c.x, u.y - c.y) < self.melee_reach),
                          key=lambda u: math.hypot(u.x - c.x, u.y - c.y))[:3]
            in_contact = bool(near) and math.hypot(near[0].x - c.x, near[0].y - c.y) < CONTACT
            if not in_contact and math.hypot(c.x - tx, c.y - ty) > 9.0:
                continue
            for u in near:
                taken.add(u)
                u.formation.detach(u, 1.0)
                if u.order is None or u.order.target is not c:
                    cmd.attack(u, c)
            engaged += bool(near)
        if engaged:
            self.ann.say(cmd, "melee", "Mêlée : on encercle les cataphractes au contact (3 contre 1)")

    # ------------------------------------------------------------------
    # Tirailleurs
    # ------------------------------------------------------------------
    def _skirmish(self, cmd: Commander, tx: float, ty: float,
                  hcas: Sequence[BaseUnit], catas: Sequence[BaseUnit]) -> None:
        if not self.skirmishers:
            return
        c = cmd.castle
        ax, ay, _ = unit_vector(tx, ty, c.x, c.y)       # axe trébuchets -> château
        harass_r = 9.0 + self.aggressiveness / 12.0
        leash = 4.5 + self.aggressiveness / 15.0
        threats = [h for h in hcas if math.hypot(h.x - tx, h.y - ty) < harass_r]
        for f in self.skirmishers:
            if not f.size:
                continue
            side = self.skirmish_side[f]
            mine = [h for h in threats
                    if ((h.x - tx) * -ay + (h.y - ty) * ax) * side >= 0] or threats
            fx, fy = f.centroid() or (f.x, f.y)
            # archer immobile en train de tirer et à portée de course : on le rattrape
            sitting, ds = cmd.nearest(fx, fy, [h for h in hcas
                                                if h.is_busy_attacking(cmd.time)
                                                or h.pending_target is not None])
            if sitting is not None and ds < 6.0 + self.aggressiveness / 12.0:
                gx, gy = sitting.x, sitting.y
                f.status = "ASSAUT"
                self.ann.say(cmd, f.name, f"{f.name} : fond sur des archers immobiles")
            elif mine and self.chase:
                hx, hy = cmd.centroid(mine)
                ux, uy, d = unit_vector(tx, ty, hx, hy)
                d = min(d, leash)
                gx, gy = tx + ux * d, ty + uy * d
                f.status = "CHASSE"
                self.ann.say(cmd, f.name, f"{f.name} : repousse les archers à cheval de son flanc")
            else:
                # en garde sur le flanc, un peu en avant
                gx = tx + (-ay * side) * 4.0 + ax * 1.0
                gy = ty + (ax * side) * 4.0 + ay * 1.0
                f.status = "GARDE"
                self.ann.say(cmd, f.name, f"{f.name} : en garde sur le flanc")
            gx, gy = self._keep_out(cmd, f, gx, gy)
            f.move_to(gx, gy)
            if math.hypot(gx - fx, gy - fy) > 0.5:
                self._face(f, math.atan2(gy - fy, gx - fx))
            # densité : serré contre les flèches, ouvert contre le piétinement
            _, dc = cmd.nearest(fx, fy, catas)
            if f.status == "ASSAUT":
                # en Shield Wall, une flèche ne fait qu'1 dégât : on marche sur les archers
                if not f.is_dense() and dc > 3.0:
                    self._make_dense(f)
                elif f.is_dense() and dc < 3.0:
                    self._make_open(f)
            elif f.is_dense() and dc < self.cata_alert - 2:
                self._make_open(f)
            elif not f.is_dense() and dc > self.cata_alert + 1:
                self._make_dense(f)
