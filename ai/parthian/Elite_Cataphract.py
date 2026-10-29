class Elite_Cataphract:
    def __init__(self):
        self.HP = 150
        self.Melee_attack = 14
        self.Melee_armour = 5
        self.Pierce_armour = 5
        self.range = 0
        self.speed = 1.35
        self.reload_time = 1.7 #en seconde
        self.attack_animation = 1.36
        self.unit_collision_radius = 0.25
        self.collision_diameter = 0.5
        

    def attack(self, target): #la target est la personne avec qui self est en contact
        damage = self.Melee_attack - target.Melee_armour
        if damage < 1:
            damage = 1
        target.HP -= damage
        #besoin de la carte pour la suite car il faut récupérer la position de tout les
        #ennemies à 0.5 unit de self (soit 0.75 du centre de self), car eux aussi prnnent
        #des dégats

    def is_alive(self):
        return self.HP > 0