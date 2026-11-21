"""Général romiain BEDLAM : chaque unité attaque l'ennemi le plus proche.

Pas de stratégie, pas de groupe : chacun pour soi. Le sujet demande que
Crassus fasse mieux que cette IA.
"""

from engine.units.trebuchet import Trebuchet

class BEDLAMCrassus:

    nom = "BEDLAM Crassus"
    PERIODE = 0.5   # on recalcule les cibles toutes les 0.5 s

    def __init__(self):
        self.prochaine_decision = 0.0
        self.journal = []

    def decide(self, engine):
        t = engine.current_time
        if t < self.prochaine_decision:
            return
        self.prochaine_decision = t + self.PERIODE

        parth = engine.get_alive_units("PARTHIAN")
        if not parth:
            return

        if not self.journal:
            self.journal.append("BEDLAM : chaque unité attaque l'ennemi le plus proche")

        for unite in engine.get_alive_units("ROMAN"):
            # L'ennemi le plus proche (min avec la distance comme critère)
            cible = min(parth, key=unite.distance)
            unite.target = cible

            if isinstance(unite, Trebuchet) and unite.is_in_range(cible):
                # Un Trebuchet qui est à portée de sa cible ne bouge pas
                unite.destination = None
            else:
                # Sinon on va vers la cible
                unite.destination = (cible.x, cible.y)