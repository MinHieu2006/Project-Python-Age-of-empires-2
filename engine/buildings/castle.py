
import math


class Castle:
    def __init__(self, x, y):
        # Position du château
        self.x = x
        self.y = y

        # Points de vie
        self.hp = 10000
        self.max_hp = 10000

        # Caractéristiques de combat
        self.pierce_armor = 13
        self.attack = 15
        self.attack_range = 11
        self.reload_time = 2
        self.volley_size = 5

        # Temps du prochain tir autorisé
        self.next_attack_time = 0

    # Compatibilité avec les unités du groupe
    @property
    def HP(self):
        return self.hp

    @HP.setter
    def HP(self, value):
        self.hp = max(0, value)

    @property
    def Pierce_armour(self):
        return self.pierce_armor

    def get_pierce_armour(self):
        return self.pierce_armor

    # Gestion des dégâts
    def take_damage(self, damage):
        self.hp = max(0, self.hp - damage)

    def receive_pierce_attack(self, attack, bonus=0):
        damage = max(
            1,
            max(0, attack - self.pierce_armor) + bonus
        )

        self.take_damage(damage)
        return damage

    # État du château
    def is_destroyed(self):
        return self.hp == 0

    def is_alive(self):
        return not self.is_destroyed()

    # Portée
    def is_in_range(self, target_x, target_y):
        distance = math.hypot(
            target_x - self.x,
            target_y - self.y
        )

        return distance <= self.attack_range

    # Rechargement
    def can_attack(self, current_time):
        return (
            self.is_alive()
            and current_time >= self.next_attack_time
        )

    # Déclenchement d'une volée
    def fire(self, current_time, target_x, target_y):
        if not self.can_attack(current_time):
            return 0

        if not self.is_in_range(target_x, target_y):
            return 0

        self.next_attack_time = (
            current_time + self.reload_time
        )

        return self.volley_size
