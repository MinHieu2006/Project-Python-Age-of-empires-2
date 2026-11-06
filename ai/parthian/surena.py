"""SURENA : général parthe conscient des formations.

Idée générale (section 75 du sujet) :
  * les ARCHERS À CHEVAL forment deux lignes ouvertes qui tournent autour des
    trébuchets à la limite de leur portée, tirent en priorité sur les
    trébuchets puis sur les légionnaires hors Shield Wall, et décrochent
    individuellement dès qu'un légionnaire s'approche (ils sont plus rapides) ;
    les deux groupes attaquent par des flancs opposés pour étirer l'armée
    romaine ;
  * les CATAPHRACTES restent groupés en coin hors de portée, cherchent
    l'angle d'approche où le moins de légionnaires barrent la route vers un
    trébuchet, s'y placent, puis chargent quand le passage est assez libre ;
    à défaut, ils écrasent un petit groupe de légionnaires isolé et serré
    (piétinement) ; un cataphracte trop blessé se replie ;
  * quand le harcèlement a assez usé l'infanterie (rapport de forces
    favorable), ASSAUT GÉNÉRAL : les cataphractes ouvrent l'escorte et
    frappent les trébuchets, les archers abattent les légionnaires hors
    Shield Wall.

Paramètres :
  aggressiveness (0-100) : nombre de bloqueurs tolérés pour charger,
      distance de harcèlement ;
  kite_distance : distance à laquelle un archer décroche ;
  retreat_hp : fraction de PV sous laquelle un cataphracte se replie ;
  assault_ratio : rapport (PV parthes / PV des légionnaires) à partir duquel
      Surena lance l'assaut général (par défaut 1.35 - aggressiveness/200,
      soit 1.1 : réglé pour un match équilibré face à Crassus).
"""

import math

from ai.shared.general import General
from ai.shared.tactics import Announcer, blockers_on_path, clusters, unit_vector
from engine.constants import CATAPHRACT, CAVALRY_ARCHER, LEGIONARY, TREBUCHET
from engine.formations.formation import SPREAD_SPACING

STAGE_RADIUS = 10.0
N_ANGLES = 16


class Surena(General):
    name = "SURENA"

    def __init__(self, aggressiveness=50, kite_distance=3.6, retreat_hp=0.3,
                 standoff=7.2, max_blockers=None, assault_ratio=None):
        super().__init__(aggressiveness=aggressiveness, kite_distance=kite_distance,
                         retreat_hp=retreat_hp, standoff=standoff, max_blockers=max_blockers,
                         assault_ratio=assault_ratio)
        # Assaut général quand nos PV dépassent ceux des légionnaires de ce rapport
        self.assault_ratio = (assault_ratio if assault_ratio is not None
                              else 1.35 - aggressiveness / 200.0)
        self.assault = False
        self.aggressiveness = aggressiveness
        self.kite_distance = kite_distance
        self.retreat_hp = retreat_hp
        self.standoff = standoff
        self.max_blockers = max_blockers if max_blockers is not None else 1 + aggressiveness // 34
        self.ann = Announcer()
        self.charging = set()
        self.charge_target = {}
        self.orbit_shift = 0.0
        self.stage = None

    # ------------------------------------------------------------------
    def setup(self, cmd):
        hcas = cmd.my_units(CAVALRY_ARCHER)
        catas = cmd.my_units(CATAPHRACT)
        trebs = cmd.enemy_units(TREBUCHET)
        tx, ty = cmd.centroid(trebs) if trebs else (cmd.castle.x, cmd.castle.y)
        c = cmd.castle
        ax, ay, _ = unit_vector(c.x, c.y, tx, ty)
        # deux groupes, gauche et droite de l'axe château -> Romains
        left = [h for h in hcas if (h.x - c.x) * -ay + (h.y - c.y) * ax >= 0]
        right = [h for h in hcas if h not in left]
        if not left or not right:
            half = len(hcas) // 2
            left, right = hcas[:half], hcas[half:]
        self.hca_groups = []
        for side, g, name in ((1, left, "Archers gauche"), (-1, right, "Archers droite")):
            if not g:
                continue
            f = cmd.formation(g, shape="line", name=name, ranks=1, spacing=SPREAD_SPACING,
                              engage=8.0, prefer=(TREBUCHET, LEGIONARY))
            f.side = side
            self.hca_groups.append(f)
        self.catas = cmd.formation(catas, shape="wedge", name="Cataphractes", spacing=0.6,
                                   engage=0.0)
        cmd.log(f"Plan : {len(hcas)} archers en deux ailes, {len(catas)} cataphractes "
                f"en réserve ; charge si <= {self.max_blockers} bloqueurs")

    # ------------------------------------------------------------------
    def decide(self, cmd):
        trebs = cmd.enemy_units(TREBUCHET)
        if not trebs:
            return
        legs = cmd.enemy_units(LEGIONARY)
        tx, ty = cmd.centroid(trebs)
        mine_hp = sum(u.HP for u in cmd.my_units())
        legs_hp = sum(u.HP for u in legs) or 1
        if not self.assault and mine_hp / legs_hp >= self.assault_ratio:
            self.assault = True
            cmd.log(f"ASSAUT GÉNÉRAL : rapport de forces {mine_hp / legs_hp:.2f} "
                    f"(seuil {self.assault_ratio:.2f})")
        if self.assault:
            self._assault(cmd, trebs, legs, tx, ty)
            return
        self.orbit_shift += 0.03          # les ailes tournent lentement
        self._archers(cmd, trebs, legs, tx, ty)
        self._cataphracts(cmd, trebs, legs, tx, ty)

    # ------------------------------------------------------------------
    def _archers(self, cmd, trebs, legs, tx, ty):
        c = cmd.castle
        base = math.atan2(c.y - ty, c.x - tx)       # côté château vu des trébuchets
        cata_ang = math.atan2(self.catas.y - ty, self.catas.x - tx) if self.catas.size else None
        for i, f in enumerate(self.hca_groups):
            if not f.size:
                continue
            if i == 0 and cata_ang is not None:
                # appui : tirer sur la zone que les cataphractes vont percer
                ang = cata_ang + 0.35 * math.sin(self.orbit_shift * 2)
                role = "appui des cataphractes"
            else:
                # diversion : flanc opposé, qui oscille pour étirer les Romains
                swing = 1.2 + 0.5 * math.sin(self.orbit_shift + (0 if f.side > 0 else math.pi))
                ang = (cata_ang + math.pi if cata_ang is not None else base + f.side * swing) \
                    + 0.6 * math.sin(self.orbit_shift)
                role = "diversion"
            r = self.standoff
            gx, gy = tx + r * math.cos(ang), ty + r * math.sin(ang)
            # si des légionnaires tiennent ce point, on recule
            _, dl = cmd.nearest(gx, gy, legs)
            if dl < self.kite_distance + 1.0:
                r += 3.0
                gx, gy = tx + r * math.cos(ang), ty + r * math.sin(ang)
                f.status = "RECUL"
            else:
                f.status = "HARCÈLEMENT"
            if not cmd.map.circle_is_free(gx, gy, 0.6):
                gx, gy = tx + (r + 4) * math.cos(ang), ty + (r + 4) * math.sin(ang)
            f.move_to(gx, gy)
            f.face_towards(tx, ty)
            self.ann.say(cmd, f.name, f"{f.name} : {role}, {f.status.lower()}")

            # décrochage individuel (kiting)
            for h in f.members:
                leg, d = cmd.nearest(h.x, h.y, legs)
                if leg is not None and d < self.kite_distance:
                    ux, uy, _ = unit_vector(leg.x, leg.y, h.x, h.y)
                    # fuir en s'écartant un peu sur le côté pour contourner
                    px, py = -uy * f.side, ux * f.side
                    f.detach(h, 1.5)
                    cmd.move(h, h.x + (ux * 0.8 + px * 0.6) * 3.5,
                             h.y + (uy * 0.8 + py * 0.6) * 3.5)

    # ------------------------------------------------------------------
    def _assault(self, cmd, trebs, legs, tx, ty):
        """Tout le monde s'engage : les cataphractes ouvrent l'escorte puis
        frappent les trébuchets ; les archers abattent les légionnaires
        hors Shield Wall autour des trébuchets."""
        for f in [self.catas] + self.hca_groups:
            f.status = "ASSAUT"
        near = [l for l in legs if math.hypot(l.x - tx, l.y - ty) < 4.0]
        for u in self.catas.alive_members():
            self.catas.detach(u, 2.0)
            treb, dt = cmd.nearest(u.x, u.y, trebs)
            blocker, db = cmd.nearest(u.x, u.y, legs)
            tgt = treb
            if blocker is not None and db < 0.75 and dt > db + 0.6:
                tgt = blocker
            if u.order is None or u.order.target is not tgt:
                cmd.attack(u, tgt)
        exposed = [l for l in near if not l.shield_wall] or near or legs
        for f in self.hca_groups:
            for h in f.alive_members():
                f.detach(h, 2.0)
                in_range = [t for t in trebs if cmd.edge_distance(h, t) <= h.range]
                if in_range:
                    tgt = in_range[0]
                else:
                    tgt, _ = cmd.nearest(h.x, h.y, exposed)
                if tgt is not None and (h.order is None or h.order.target is not tgt):
                    cmd.attack(h, tgt)

    def _best_approach(self, cmd, trebs, legs, tx, ty, cx, cy):
        best = None
        for k in range(N_ANGLES):
            a = 2 * math.pi * k / N_ANGLES
            px, py = tx + STAGE_RADIUS * math.cos(a), ty + STAGE_RADIUS * math.sin(a)
            if not cmd.map.circle_is_free(px, py, 1.5):
                continue
            _, dl = cmd.nearest(px, py, legs)
            if dl < 3.0:
                continue
            blk = min(blockers_on_path(legs, px, py, t.x, t.y, 0.9) for t in trebs)
            score = blk + 0.04 * math.hypot(px - cx, py - cy)
            if best is None or score < best[0]:
                best = (score, blk, px, py)
        return best

    def _cataphracts(self, cmd, trebs, legs, tx, ty):
        f = self.catas
        catas = cmd.my_units(CATAPHRACT)
        if not catas:
            return

        # 1. Charge en cours : retraite des blessés, choix des cibles
        for u in list(self.charging):
            if not u.is_alive():
                self.charging.discard(u)
                continue
            if u.HP < self.retreat_hp * u.max_hp:
                self.charging.discard(u)
                f.reattach(u)
                self.ann.say(cmd, "cata-ret", "Cataphracte blessé : repli")
                continue
            tgt = self.charge_target.get(u)
            if tgt is None or not tgt.is_alive():
                tgt, _ = cmd.nearest(u.x, u.y, trebs)
                self.charge_target[u] = tgt
            f.detach(u, 2.0)
            # percée : un légionnaire barre la route -> on le renverse
            blocker, bd = cmd.nearest(u.x, u.y, legs)
            if (blocker is not None and bd < 0.75
                    and cmd.distance(u, tgt) > bd + 0.6):
                tgt = blocker
            if u.order is None or u.order.target is not tgt:
                cmd.attack(u, tgt)
        if self.charging:
            f.status = "CHARGE"
            return

        # 2. Frappe d'opportunité : un trébuchet presque sans garde
        exposed = [t for t in trebs
                   if sum(1 for l in legs if math.hypot(l.x - t.x, l.y - t.y) < 3.5) < 4]
        cen = f.centroid() or (f.x, f.y)
        if exposed and min(math.hypot(t.x - cen[0], t.y - cen[1]) for t in exposed) < 25:
            self.ann.say(cmd, "cata", "CHARGE des cataphractes : un trébuchet est sans garde")
            self._charge(cmd, f, exposed)
            return

        # 3. Repérer le meilleur angle d'approche (choix stable)
        cx, cy = f.x, f.y
        best = self._best_approach(cmd, trebs, legs, tx, ty, cx, cy)
        if best is None:
            f.status = "ATTENTE"
            return
        if self.stage is not None:
            # on garde l'angle courant sauf s'il devient nettement moins bon
            sx, sy = self.stage
            cur = min(blockers_on_path(legs, sx, sy, t.x, t.y, 0.9) for t in trebs)
            if cur <= best[1] + 1:
                best = (best[0], cur, sx, sy)
        _, blk, px, py = best
        self.stage = (px, py)
        f.move_to(px, py)
        f.face_towards(tx, ty)
        ready = math.hypot(cen[0] - px, cen[1] - py) < 4.0
        if ready and blk <= self.max_blockers:
            self.ann.say(cmd, "cata", f"CHARGE des cataphractes : passage avec {blk} bloqueur(s)")
            for u in f.alive_members():
                if u.HP >= self.retreat_hp * u.max_hp:
                    tgt, _ = cmd.nearest(u.x, u.y, trebs)
                    self.charging.add(u)
                    self.charge_target[u] = tgt
                    f.detach(u, 2.0)
                    cmd.attack(u, tgt)
            f.status = "CHARGE"
            return

        # 4. Sinon : écraser un petit groupe isolé et serré
        target_group = self._isolated_group(cmd, legs, f)
        if target_group is not None:
            gx, gy = cmd.centroid(target_group)
            self.ann.say(cmd, "cata", f"Cataphractes : piétinent un groupe isolé de "
                                      f"{len(target_group)} légionnaires")
            for u in f.alive_members():
                tgt, _ = cmd.nearest(u.x, u.y, target_group)
                f.detach(u, 1.0)
                cmd.attack(u, tgt)
            f.status = "PIÉTINEMENT"
            return

        f.status = f"MANŒUVRE ({blk} bloqueurs)"
        self.ann.say(cmd, "cata", "Cataphractes : manœuvrent vers l'angle le plus ouvert")

    def _charge(self, cmd, f, trebs):
        for u in f.alive_members():
            if u.HP >= self.retreat_hp * u.max_hp:
                tgt, _ = cmd.nearest(u.x, u.y, trebs)
                self.charging.add(u)
                self.charge_target[u] = tgt
                f.detach(u, 2.0)
                cmd.attack(u, tgt)
        f.status = "CHARGE"

    def _isolated_group(self, cmd, legs, f):
        if not legs:
            return None
        groups = clusters(legs, link=0.9)
        best, best_d = None, math.inf
        for g in groups:
            if len(g) > 10 or len(g) < 4:
                continue
            gx, gy = cmd.centroid(g)
            others = [l for l in legs if l not in g]
            _, d_other = cmd.nearest(gx, gy, others)
            if d_other < 5.0:
                continue
            d = math.hypot(gx - f.x, gy - f.y)
            if d < 12.0 and d < best_d:
                best, best_d = g, d
        return best
