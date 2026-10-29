class Legionary:
    def __init__(self, x, y, team):
        self.HP = 75
        self.Melee_attack = 16
        self.Melee_armour = 6
        self.Pierce_armour = 6
        self.range = 0
        self.speed = 1.06
        self.reload_time = 2.0
        self.attack_animation = 1.26
        self.unit_collision_radius = 0.20
        self.collision_diameter = 0.40

        # Position et camp
        self.x = x
        self.y = y
        self.team = team

        # Shield Wall : vrai si au moins 4 autres légionnaires sont à 0.42 ou moins
        self.shield_wall = False

    def is_alive(self):
        return self.HP > 0

    def attack(self, target):
        damage = self.Melee_attack - target.Melee_armour
        if damage < 1:
            damage = 1
        target.HP -= damage

    def get_pierce_armour(self):
        # +6 d'armure de perce avec le Shield Wall
        if self.shield_wall:
            return self.Pierce_armour + 6
        return self.Pierce_armour

    def distance(self, other):
        # distance entre deux unités
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

    