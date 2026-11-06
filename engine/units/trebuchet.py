import random
from dataclasses import dataclass

from engine.units.base_unit import BaseUnit


# États possibles du trébuchet
PACKED = "packed"          # replié : peut se déplacer, ne peut pas tirer
UNPACKING = "unpacking"    # en cours de déploiement (11 s)
UNPACKED = "unpacked"      # déployé : peut tirer, ne peut pas bouger
PACKING = "packing"        # en cours de repli (11 s)


@dataclass
class TrebuchetShot:
    """Tir sorti du trébuchet, à transmettre au moteur / à l'affichage
    (pour dessiner le projectile)."""
    shooter: "Trebuchet"
    target: object
    origin: tuple
    impact: tuple
    hit: bool
    damage: int
    time: float


class Trebuchet(BaseUnit):
    """Trébuchet romain (stats du sujet, section 72.6)."""

    PIERCE_ATTACK = 200
    BONUS_VS_BUILDINGS = 250
    MIN_RANGE = 4.0
    PACKING_TIME = 11.0
    ACCURACY_VS_BUILDINGS = 0.80
    ACCURACY_VS_UNITS = 0.15

    def __init__(self, x, y, team, rng=None):
        super().__init__(
            x, y, team,
            hp=150,
            pierce_attack=self.PIERCE_ATTACK,
            melee_armour=2,
            pierce_armour=8,
            attack_range=16.0,
            speed=0.80,
            reload_time=10.0,
            attack_animation=1.0,
            collision_radius=0.50,
        )
        self.min_range = self.MIN_RANGE
        self.bonus_vs_buildings = self.BONUS_VS_BUILDINGS

        # Comme dans AoE2, le trébuchet apparaît replié
        self.state = PACKED
        self.state_change_end = 0.0

        # Tir en cours : les dégâts sortent à la fin de l'animation
        self.pending_target = None

        # Générateur aléatoire injectable (seed => simulation déterministe)
        self.rng = rng if rng is not None else random.Random()

    # ------------------------------------------------------------------
    # Repli / déploiement
    # ------------------------------------------------------------------
    def is_packed(self):
        return self.state == PACKED

    def is_unpacked(self):
        return self.state == UNPACKED

    def is_transitioning(self):
        return self.state in (PACKING, UNPACKING)

    def unpack(self, current_time):
        """Commence le déploiement (11 s). Renvoie True si l'ordre est pris."""
        if not self.is_alive() or self.state != PACKED:
            return False
        self.state = UNPACKING
        self.state_change_end = current_time + self.PACKING_TIME
        self.destination = None
        return True

    def pack(self, current_time):
        """Commence le repli (11 s). Annule un tir en préparation."""
        if not self.is_alive() or self.state != UNPACKED:
            return False
        self.state = PACKING
        self.state_change_end = current_time + self.PACKING_TIME
        self.pending_target = None
        self.target = None
        return True

    # ------------------------------------------------------------------
    # Déplacement
    # ------------------------------------------------------------------
    def can_move(self, current_time=0.0):
        return self.is_alive() and self.state == PACKED

    def move_towards(self, target_x, target_y, delta_time, current_time=0.0):
        # Un trébuchet déployé (ou en transition) ne bouge pas
        if not self.can_move(current_time):
            return
        super().move_towards(target_x, target_y, delta_time, current_time)

    # ------------------------------------------------------------------
    # Portée
    # ------------------------------------------------------------------
    @staticmethod
    def target_radius(target):
        """Rayon de la cible : la portée se mesure jusqu'au bord de la cible."""
        if getattr(target, "is_building", False):
            return getattr(target, "footprint", 0) / 2.0
        return getattr(target, "unit_collision_radius", 0.0)

    def distance_to_target(self, target):
        return max(0.0, self.distance_to_coords(target.x, target.y)
                   - self.target_radius(target))

    def is_in_range(self, target):
        d = self.distance_to_target(target)
        return self.min_range <= d <= self.range

    # ------------------------------------------------------------------
    # Attaque
    # ------------------------------------------------------------------
    def can_attack(self, current_time):
        return (super().can_attack(current_time)
                and self.state == UNPACKED
                and self.pending_target is None)

    def attack(self, target, current_time=0.0):
        """Lance l'animation de tir (1 s). Le projectile ne part qu'à la fin
        de l'animation, via update(). Renvoie True si le tir est lancé."""
        if target is None or not target.is_alive():
            return False
        if not self.can_attack(current_time) or not self.is_in_range(target):
            return False
        self.target = target
        self.pending_target = target
        self.next_attack_time = current_time + self.reload_time
        self.is_attacking_until = current_time + self.attack_animation
        return True

    def accuracy_against(self, target):
        if getattr(target, "is_building", False):
            return self.ACCURACY_VS_BUILDINGS
        return self.ACCURACY_VS_UNITS

    def compute_damage(self, target):
        if getattr(target, "is_building", False):
            return max(1, max(0, self.Pierce_attack - target.get_pierce_armour())
                       + self.bonus_vs_buildings)
        return max(1, max(0, self.Pierce_attack - target.get_pierce_armour()))

    def _release_shot(self, current_time):
        target = self.pending_target
        self.pending_target = None
        if target is None or not target.is_alive():
            return None

        hit = self.rng.random() < self.accuracy_against(target)
        damage = 0
        impact = (target.x, target.y)
        if hit:
            if getattr(target, "is_building", False):
                damage = target.receive_pierce_attack(self.Pierce_attack,
                                                      self.bonus_vs_buildings)
            else:
                damage = target.receive_attack(pierce_damage=self.Pierce_attack)
        else:
            # Tir raté : le projectile tombe à côté (simplification : sans dégâts)
            impact = (target.x + self.rng.uniform(-1.5, 1.5),
                      target.y + self.rng.uniform(-1.5, 1.5))

        return TrebuchetShot(self, target, (self.x, self.y), impact,
                             hit, damage, current_time)

    # ------------------------------------------------------------------
    # Mise à jour à chaque tick
    # ------------------------------------------------------------------
    def update(self, current_time):
        """À appeler à chaque tick. Termine les repli/déploiement et
        libère le projectile en fin d'animation. Renvoie un TrebuchetShot
        si un tir vient de partir, sinon None."""
        if not self.is_alive():
            self.pending_target = None
            return None

        if self.is_transitioning() and current_time >= self.state_change_end:
            self.state = UNPACKED if self.state == UNPACKING else PACKED

        if self.pending_target is not None and current_time >= self.is_attacking_until:
            return self._release_shot(current_time)
        return None
