import math


class BaseUnit:
    """Base class for all combat units in the simulation."""

    def __init__(
        self,
        x: float,
        y: float,
        team: str,
        hp: int,
        melee_attack: int = 0,
        pierce_attack: int = 0,
        melee_armour: int = 0,
        pierce_armour: int = 0,
        attack_range: float = 0.0,
        speed: float = 1.0,
        reload_time: float = 2.0,
        attack_animation: float = 1.0,
        collision_radius: float = 0.20,
    ):
        # Position and faction
        self.x = float(x)
        self.y = float(y)
        self.team = team

        # Health points
        self.max_hp = int(hp)
        self._hp = int(hp)

        # Combat attributes
        self.Melee_attack = melee_attack
        self.Pierce_attack = pierce_attack
        self.Melee_armour = melee_armour
        self.Pierce_armour = pierce_armour
        self.range = attack_range
        self.speed = speed
        self.reload_time = reload_time
        self.attack_animation = attack_animation

        # Circular collision geometry
        self.unit_collision_radius = float(collision_radius)
        self.collision_diameter = float(collision_radius) * 2.0

        # Action timers
        self.next_attack_time = 0.0
        self.is_attacking_until = 0.0

        # Target and destination
        self.destination = None
        self.target = None

    @property
    def HP(self) -> int:
        return self._hp

    @HP.setter
    def HP(self, value: int):
        self._hp = max(0, int(value))

    @property
    def hp(self) -> int:
        return self._hp
    
    @hp.setter
    def hp(self, value: int):
        self._hp = max(0, int(value))


    def is_alive(self) -> bool:
        return self._hp > 0

    def get_melee_armour(self) -> int:
        return self.Melee_armour

    def get_pierce_armour(self) -> int:
        return self.Pierce_armour

    def distance(self, other) -> float:
        # Euclidean distance to another unit
        return math.hypot(self.x - other.x, self.y - other.y)

    def distance_to(self, other) -> float:
        return self.distance(other)

    def distance_to_coords(self, target_x: float, target_y: float) -> float:
        return math.hypot(self.x - target_x, self.y - target_y)

    def is_in_contact(self, other, tolerance: float = 0.05) -> bool:
        if not self.is_alive() or not other.is_alive():
            return False
        gap = self.distance(other) - self.unit_collision_radius - other.unit_collision_radius
        return gap <= tolerance

    def take_damage(self, damage: int) -> int:
        # Deduct damage directly from HP without reapplying armour
        actual_damage = max(1, int(damage))
        self.hp = max(0, self.hp - actual_damage)
        return actual_damage

    def receive_attack(self, melee_damage: int = 0, pierce_damage: int = 0, bonus: int = 0) -> int:
        # Standard combat formula: Damage = max(1, sum(max(0, Attack - Armour)) + bonus)
        net_melee = max(0, melee_damage - self.get_melee_armour())
        net_pierce = max(0, pierce_damage - self.get_pierce_armour())
        total_damage = max(1, net_melee + net_pierce + bonus)
        return self.take_damage(total_damage)

    def receive_arrow(self, pierce_attack: int) -> int:
        return self.receive_attack(pierce_damage=pierce_attack)

    def can_attack(self, current_time: float) -> bool:
        return self.is_alive() and current_time >= self.next_attack_time

    def is_busy_attacking(self, current_time: float) -> bool:
        # Cannot move while attack animation is active
        return current_time < self.is_attacking_until

    def attack(self, target, current_time: float = 0.0):
        if not self.is_alive() or not target.is_alive() or not self.can_attack(current_time):
            return None
        damage = target.receive_attack(melee_damage=self.Melee_attack)
        self.next_attack_time = current_time + self.reload_time
        self.is_attacking_until = current_time + self.attack_animation
        return damage

    def move_towards(self, target_x: float, target_y: float, delta_time: float, current_time: float = 0.0):
        # Dead units or units locked in attack animation cannot move
        if not self.is_alive() or self.is_busy_attacking(current_time):
            return

        distance = self.distance_to_coords(target_x, target_y)
        if distance == 0:
            return

        move_distance = self.speed * delta_time
        if move_distance >= distance:
            self.x = target_x
            self.y = target_y
            self.destination = None
        else:
            # Move towards target along normalized direction vector
            ratio = move_distance / distance
            self.x += (target_x - self.x) * ratio
            self.y += (target_y - self.y) * ratio
