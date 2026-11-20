def calculate_pierce_damage(attack, armor, bonus=0):
    damage = max(1, max(0, attack - armor) + bonus)
    return damage
def apply_pierce_attack(attacker, target, bonus=0):
    if not attacker.is_alive() or not target.is_alive():
        return 0

    attack = attacker.Pierce_attack

    damage = calculate_pierce_damage(
        attack,
        target.get_pierce_armour(),
        bonus
    )

    target.take_damage(damage)

    return damage