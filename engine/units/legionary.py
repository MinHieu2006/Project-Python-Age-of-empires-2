from engine.units.base_unit import BaseUnit                                                       
class Legionary(BaseUnit):
    def __init__(self, x: float, y: float, team: str = "ROMAN"):
        super().__init__(                                                                         
                x=x,                                                                                  
                y=y,
                team=team,
                hp=75,                                                                                
                melee_attack=16,                                                                      
                pierce_attack=0,                                                                      
                melee_armour=6,                                                                       
                pierce_armour=6,                                                                      
                attack_range=0.0,
                speed=1.06,
                reload_time=2.0,
                attack_animation=1.26,
                collision_radius=0.20,                                                                
        )        
        # Shield Wall : vrai si au moins 4 autres légionnaires sont à 0.42 ou moins
        self.shield_wall = False

        # Pour le déplacement et la cible
        self.destination = None
        self.target = None


    def is_alive(self):
        return self.HP > 0

    def get_pierce_armour(self):
        # +6 d'armure de perce avec le Shield Wall
        if self.shield_wall:
            return self.Pierce_armour + 6
        return self.Pierce_armour

    def distance(self, other):
        # distance entre deux unités
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5


    def update_shield_wall(self, all_units):
        # On compte les autres légionnaires vivants de notre camp à 0.42 ou moins
        neighbours = 0
        for other in all_units:
            if other is self:
                continue
            if isinstance(other, Legionary) and other.team == self.team and other.is_alive():
                if self.distance(other) <= 0.42:
                    neighbours += 1
        self.shield_wall = neighbours >= 4


    