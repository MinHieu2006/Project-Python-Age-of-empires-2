#effectue uniquement un calcul
def calculate_pierce_damage(attack, armor, bonus=0):
    damage = max(1, max(0, attack - armor) + bonus)
    return damage
#récupère les caractéristiques de l'attaquant et de la cible, applique le calcul de dégâts et met à jour les points de vie de la cible
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
#Calcule les dégâts de mêlée et perforants, avec bonus éventuel
def calculate_damage(
    melee_attack,
    pierce_attack,
    melee_armor,
    pierce_armor,
    bonus=0
):
    melee_damage = max(0, melee_attack - melee_armor)

    pierce_damage = max(0, pierce_attack - pierce_armor)

    total_damage = melee_damage + pierce_damage + bonus

    return max(1, total_damage)