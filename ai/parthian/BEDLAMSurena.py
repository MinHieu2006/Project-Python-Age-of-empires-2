"""Général parthe BEDLAM : chaque unité attaque l'ennemi le plus proche.

Pas de stratégie, pas de groupe : chacun pour soi. Le sujet demande que
Surena fasse mieux que cette IA.
"""

from engine.units.cavalry_archer import Cavalry_Archer


class BEDLAMSurena:

    nom = "BEDLAM Surena"
    PERIODE = 0.5   # on recalcule les cibles toutes les 0.5 s

    def __init__(self):
        self.prochaine_decision = 0.0
        self.journal = []

    def decide(self, engine):
        t = engine.current_time
        if t < self.prochaine_decision:
            return
        self.prochaine_decision = t + self.PERIODE

        romains = engine.get_alive_units("ROMAN")
        if not romains:
            return

        if not self.journal:
            self.journal.append("BEDLAM : chaque unité attaque l'ennemi le plus proche")

        for unite in engine.get_alive_units("PARTHIAN"):
            # L'ennemi le plus proche (min avec la distance comme critère)
            cible = min(romains, key=unite.distance)
            unite.target = cible

            if isinstance(unite, Cavalry_Archer) and unite.is_in_range(cible):
                # Un archer à portée s'arrête pour tirer
                unite.destination = None
            else:
                # Sinon on va vers la cible
                unite.destination = (cible.x, cible.y)