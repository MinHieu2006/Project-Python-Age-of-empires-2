from engine.units.base_unit import BaseUnit                                                       
class Cavalry_Archer(BaseUnit):
    """Parthian mobile ranged cavalry unit."""
    def __init__(self, x: float, y: float, team: str = "PARTHIAN"):
        super().__init__(
            x=x,
            y=y,
            team=team,
            hp=80,
            melee_attack=0,
            pierce_attack=12,
            melee_armour=5,
            pierce_armour=6,
            attack_range=8.0,
            speed=1.44,
            reload_time=1.8,
            attack_animation=1.17,
            collision_radius=0.25,
        )
    def is_in_range(self, target) -> bool:
        # Check if the target is within attack range
        return self.distance(target) <= self.range
    def attack(self, target, current_time: float = 0.0):
        if not self.is_alive() or not target.is_alive() or not self.can_attack(current_time):
            return None # Cannot attack if either unit is dead

        if not self.is_in_range(target):
            return None # Target is out of range

        if hasattr(target, 'receive_arrow'):
            damage = target.receive_arrow(self.Pierce_attack)
        elif hasattr(target, 'receive_pierce_attack'):
            damage = target.receive_pierce_attack(self.Pierce_attack)
        else:
            damage = target.receive_pierce_attack(pierce_attack=self.Pierce_attack)

        self.next_attack_time = current_time + self.reload_time
        self.is_attacking_until = current_time + self.attack_animation
        return damage

# Aliases for flexibility
HeavyCavalryArcher = Cavalry_Archer
CavalryArcher = Cavalry_Archer