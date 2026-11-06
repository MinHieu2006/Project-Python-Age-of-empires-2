"""CRASSUS : général romain conscient des formations.

Idée générale (section 74 du sujet) :
  * les trébuchets avancent en bloc vers une position de tir choisie hors de
    portée du château, du côté romain ;
  * une ESCORTE de légionnaires forme un anneau autour d'eux, assez serré
    (écart < 0.5) pour qu'aucun cataphracte ne puisse passer ;
  * un ÉCRAN se place entre les trébuchets et les cataphractes : dense
    (Shield Wall) tant que les flèches sont la menace, ouvert sur deux rangs
    décalés dès que les cataphractes approchent (moins de piétinement, plus
    de largeur, toujours infranchissable) ;
  * des groupes de TIRAILLEURS denses repoussent les archers à cheval qui
    s'approchent des trébuchets, sans jamais s'éloigner au-delà d'une laisse ;
  * personne ne s'aventure à portée du château.

Paramètres :
  aggressiveness (0-100) : longueur de la laisse des tirailleurs et
      distance de poursuite des archers ;
  screen_distance : distance de l'écran devant les trébuchets ;
  cata_alert : distance des cataphractes à laquelle l'écran s'ouvre ;
  skirmish_groups : nombre de groupes de tirailleurs.
"""

import math

from ai.shared.general import General
from ai.shared.tactics import Announcer, keep_out_of_castle, unit_vector
from engine.constants import CATAPHRACT, CAVALRY_ARCHER, LEGIONARY, TREBUCHET
from engine.formations.formation import DENSE_SPACING

CASTLE_SAFE = 2.0 + 11.0 + 0.9      # bord du château + portée + marge
SPREAD = 1.0                        # écart de l'écran ouvert
RING_GAP = 0.82                     # écart max dans l'anneau (catas : 0.5 de diamètre)


class Crassus(General):
    name = "CRASSUS"

    def __init__(self, aggressiveness=50, screen_distance=3.5, cata_alert=8.0,
                 skirmish_groups=2, skirmish_size=8):
        super().__init__(aggressiveness=aggressiveness, screen_distance=screen_distance,
                         cata_alert=cata_alert, skirmish_groups=skirmish_groups,
                         skirmish_size=skirmish_size)
        self.aggressiveness = aggressiveness
        self.screen_distance = screen_distance
        self.cata_alert = cata_alert
        self.n_skirmish = skirmish_groups
        self.skirmish_size = skirmish_size
        self.ann = Announcer()
        self.firing_point = None
        self.siege = False
        self.formed = False
        self.halt_since = None

    # ------------------------------------------------------------------
    def setup(self, cmd):
        trebs = cmd.my_units(TREBUCHET)
        legs = cmd.my_units(LEGIONARY)
        c = cmd.castle
        rx, ry = cmd.centroid(cmd.my_units())
        ux, uy, _ = unit_vector(c.x, c.y, rx, ry)
        fire_d = c.footprint / 2 + trebs[0].range - 1.6 if trebs else 15.0
        self.firing_point = (c.x + ux * fire_d, c.y + uy * fire_d)
        self.toward_castle = math.atan2(-uy, -ux)

        # Trébuchets : petit bloc compact
        self.trebs = cmd.formation(trebs, shape="wedge", name="Trébuchets", spacing=1.5)
        self.trebs.move_to(*self.firing_point, facing=self.toward_castle)
        self.trebs.max_error = 1.5
        self.trebs.speed_factor = 0.85      # l'ancrage attend les trébuchets

        # Répartition des légionnaires
        legs = sorted(legs, key=lambda u: math.hypot(u.x - rx, u.y - ry))
        cluster_r = 0.8 * math.sqrt(max(len(trebs), 1)) + 0.5
        ring_r = cluster_r + 0.9
        n_ring = min(len(legs), math.ceil(2 * math.pi * ring_r / RING_GAP))
        ring = legs[:n_ring]
        rest = legs[n_ring:]
        groups = []
        for _ in range(self.n_skirmish):
            if len(rest) >= self.skirmish_size + 8:
                groups.append(rest[:self.skirmish_size])
                rest = rest[self.skirmish_size:]
        screen = rest

        self.ring_r = ring_r
        self.escort_target = len(ring)
        self.escort = cmd.formation(ring, shape="circle", name="Escorte",
                                    spacing=2 * math.pi * (ring_r + 2.5) / max(len(ring), 1),
                                    radius=ring_r + 2.5, engage=0.12, leash=0.5,
                                    prefer=(CATAPHRACT,))
        self.escort.follow(self.trebs)
        self.screen = None
        if screen:
            self.screen = cmd.formation(screen, shape="line", name="Écran", ranks=2,
                                        spacing=DENSE_SPACING, engage=1.0, leash=1.6,
                                        prefer=(CATAPHRACT,))
        self.skirmishers = []
        for i, g in enumerate(groups):
            f = cmd.formation(g, shape="block", name=f"Tirailleurs {i + 1}", ranks=2,
                              spacing=DENSE_SPACING, engage=1.0, leash=2.5,
                              prefer=(CAVALRY_ARCHER,))
            f.side = 1 if i % 2 == 0 else -1
            self.skirmishers.append(f)
        cmd.log(f"Plan : {len(trebs)} trébuchets vers ({self.firing_point[0]:.0f}, "
                f"{self.firing_point[1]:.0f}), escorte {len(ring)}, écran {len(screen)}, "
                f"{len(groups)} groupes de tirailleurs")

    # ------------------------------------------------------------------
    def decide(self, cmd):
        trebs = cmd.my_units(TREBUCHET)
        if not trebs:
            return
        c = cmd.castle
        tx, ty = cmd.centroid(trebs)
        catas = cmd.enemy_units(CATAPHRACT)
        hcas = cmd.enemy_units(CAVALRY_ARCHER)
        near_cata, d_cata = cmd.nearest(tx, ty, catas)

        self._escort(cmd)
        self._trebuchets(cmd, trebs, near_cata, d_cata)
        self._screen(cmd, tx, ty, catas, near_cata, d_cata)
        self._skirmish(cmd, tx, ty, hcas, catas)
        self._gang_up(cmd, tx, ty, catas)

    # ------------------------------------------------------------------
    def _escort(self, cmd):
        e = self.escort
        # Pertes : on prélève des légionnaires sur l'écran pour refermer l'anneau
        if (e.size < self.escort_target and self.screen is not None
                and self.screen.size > 8):
            donor, _ = cmd.nearest(e.x, e.y, self.screen.alive_members())
            if donor is not None:
                e.add(donor)
                self.ann.say(cmd, "esc", "Escorte : un légionnaire de l'écran comble un trou")
        # Tant qu'un trébuchet n'est pas à sa place, l'anneau s'élargit pour
        # le laisser entrer ; ensuite il se resserre (infranchissable)
        cx, cy = e.centroid() or (e.x, e.y)
        outside = any(math.hypot(t.x - cx, t.y - cy) > self.ring_r - 0.4
                      for t in self.trebs.alive_members())
        _, d_cata = cmd.nearest(cx, cy, cmd.enemy_units(CATAPHRACT))
        loose = outside and d_cata > 10.0 and not self.siege
        r = self.ring_r + (2.5 if loose else 0.0)
        if e.size and abs((e.radius or 0) - r) > 1e-6:
            e.set_shape("circle", spacing=2 * math.pi * r / e.size, radius=r)
            e.status = "OUVERT" if loose else "FERMÉ"

    def _trebuchets(self, cmd, trebs, near_cata, d_cata):
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
        # Rassemblement : on ne part pas avant que l'escorte entoure les trébuchets
        if not self.formed:
            ready = (self.trebs.cohesion() < 0.8 and self.escort.cohesion() < 0.8
                     and (self.escort.radius or 0) <= self.ring_r + 1e-6)
            if self.escort.size == 0 or (ready and cmd.time > 3) or cmd.time > 25:
                self.formed = True
            else:
                tf.speed_factor = 0.0
                self.ann.say(cmd, "treb", "Rassemblement : l'escorte se met en place")
                return
        # Cataphractes en approche : halte pour que l'anneau se referme
        # (un anneau immobile est étanche, un anneau en marche l'est moins).
        # Halte limitée à 20 s pour ne pas se laisser bloquer indéfiniment.
        if near_cata is not None and d_cata < 8.0:
            if self.halt_since is None:
                self.halt_since = cmd.time
            if cmd.time - self.halt_since < 20.0:
                tf.speed_factor = 0.0
                self.ann.say(cmd, "treb", "Trébuchets : halte, anneau fermé face aux cataphractes")
                return
        elif d_cata > 11.0:
            self.halt_since = None
        # Marche : l'escorte doit suivre, sinon on ralentit
        if self.escort.size and self.escort.cohesion() > 0.6:
            tf.speed_factor = 0.4
            self.ann.say(cmd, "treb", "Trébuchets : on attend que l'escorte se reforme")
        else:
            tf.speed_factor = 0.85
            self.ann.say(cmd, "treb", "Trébuchets : en marche vers la position de tir")

    def _screen(self, cmd, tx, ty, catas, near_cata, d_cata):
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
            s.spread(SPREAD, ranks=2)
            s.status = "REPLI"
            self.ann.say(cmd, "screen", "Écran : repli pour couvrir les trébuchets")
            return

        s.place_between((tx, ty), (thx, thy), self.screen_distance)
        gx, gy = keep_out_of_castle(cmd, *s.goal, CASTLE_SAFE)
        s.goal = (gx, gy)

        sx, sy = s.x, s.y
        _, d_screen = cmd.nearest(sx, sy, catas)
        if s.is_dense() and d_screen < self.cata_alert:
            s.spread(SPREAD, ranks=2)
            self.ann.say(cmd, "screen", f"Écran : OUVERT (cataphractes à {d_screen:.1f})")
        elif not s.is_dense() and d_screen > self.cata_alert + 2.5:
            s.tighten(ranks=2)
            self.ann.say(cmd, "screen", "Écran : SHIELD WALL (flèches)")
        s.status = "DENSE" if s.is_dense() else "OUVERT"

    def _gang_up(self, cmd, tx, ty, catas):
        """Mêlée locale : un cataphracte au contact de nos lignes est encerclé
        par les 3 légionnaires libres les plus proches (l'escorte, elle,
        ne quitte jamais l'anneau sauf si l'ennemi est déjà à l'intérieur)."""
        free = []
        for f in [self.screen] + self.skirmishers:
            if f is not None:
                free.extend(f.alive_members())
        ex, ey = self.escort.centroid() or (tx, ty)
        inside = [c for c in catas if math.hypot(c.x - ex, c.y - ey) < self.ring_r - 0.3]
        if inside:
            free.extend(self.escort.alive_members())
        taken = set()
        engaged = 0
        for c in sorted(catas, key=lambda c: math.hypot(c.x - tx, c.y - ty)):
            if math.hypot(c.x - tx, c.y - ty) > 9.0:
                continue
            near = sorted((u for u in free if u not in taken
                           and math.hypot(u.x - c.x, u.y - c.y) < 2.5),
                          key=lambda u: math.hypot(u.x - c.x, u.y - c.y))[:3]
            for u in near:
                taken.add(u)
                u.formation.detach(u, 1.0)
                if u.order is None or u.order.target is not c:
                    cmd.attack(u, c)
            engaged += bool(near)
        if engaged:
            self.ann.say(cmd, "melee", "Mêlée : on encercle les cataphractes au contact (3 contre 1)")

    def _skirmish(self, cmd, tx, ty, hcas, catas):
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
            side = f.side
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
            elif mine:
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
            gx, gy = keep_out_of_castle(cmd, gx, gy, CASTLE_SAFE)
            f.move_to(gx, gy)
            # densité : serré contre les flèches, ouvert contre le piétinement
            _, dc = cmd.nearest(fx, fy, catas)
            if f.status == "ASSAUT":
                # en Shield Wall, une flèche ne fait qu'1 dégât : on marche sur les archers
                if not f.is_dense() and dc > 3.0:
                    f.tighten(ranks=2)
                elif f.is_dense() and dc < 3.0:
                    f.spread(SPREAD, ranks=2)
            elif f.is_dense() and dc < self.cata_alert - 2:
                f.spread(SPREAD, ranks=2)
            elif not f.is_dense() and dc > self.cata_alert + 1:
                f.tighten(ranks=2)
