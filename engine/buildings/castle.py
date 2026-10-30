import math
class Castle:
    def __init__(self, x, y):
        self.x = x
        self.y = y

        self.hp = 10000
        self.max_hp = 10000

        self.pierce_armor = 13
        self.attack = 15
        self.attack_range = 11
        self.reload_time = 2
        self.next_attack_time = 0

    def take_damage(self, damage):
        self.hp = max(0, self.hp - damage)

    def is_in_range(self, target_x, target_y):
        distance = math.hypot(target_x - self.x, target_y - self.y)
        return distance <= self.attack_range    

    def receive_pierce_attack(self, attack, bonus=0):
        damage = max(1, max(0, attack - self.pierce_armor) + bonus)
        self.take_damage(damage)
        return damage

    def is_destroyed(self):
        return self.hp == 0
    
    def can_attack(self, current_time):
        return not self.is_destroyed() and current_time >= self.next_attack_time

    def fire(self, current_time, target_x, target_y):
        if not self.can_attack(current_time):
            return 0

        if not self.is_in_range(target_x, target_y):
            return 0

        self.next_attack_time = current_time + self.reload_time
        return 5
    


    