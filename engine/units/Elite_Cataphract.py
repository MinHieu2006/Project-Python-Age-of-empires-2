from engine.units.base_unit import BaseUnit                                                       
class Elite_Cataphract(BaseUnit):
    def __init__(self, x: float, y: float, team: str = "PARTHIAN"):
        super().__init__(
            x=x,
            y=y,
            team=team,
            hp=150,
            melee_attack=14,
            pierce_attack=0,
            melee_armour=5,
            pierce_armour=5,
            attack_range=0,
            speed=1.35,
            reload_time=1.7,
            attack_animation=1.36,
            collision_radius=0.25,
        )
        