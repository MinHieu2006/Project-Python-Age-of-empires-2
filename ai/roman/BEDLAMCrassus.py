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

    def _gerer_tribuchet(self, treb, cibles, t):
        if treb.is_transitioning(): #si le tribuchet packing ou unpaccking on farit rien
            return

        a_portee = [c for c in cibles if treb.is_in_range(c)] #on prend toutes les cibles à portée du trebuchet
        if a_portee: #si la liste n'est pas vide
            treb.target = min(a_portee, key=treb.distance_to_target) #la cible est la plus proche de toutes les cibles à portée
            treb.destination = None #on s'arrete
            if treb.is_packed(): #on s'unpack pour permettre l'attaque
                treb.unpack(t)
            return
        
        cible = min(cibles, key=treb.distance_to_target) #si personne a porte alors on prend la cible la plus proche
        if treb.distance_to_target(cible) > treb.range: #si on est trop loin pour attaquer alors on se rapproche
            if treb.is_unpacked(): #si on est unpack impossible de se deplacer alors on a se pack
                treb.pack(t)
            else: #sinon on bouge
                treb.destination = (cible.x, cible.y)
        else: #si la cible est a porte alors on att le prochain tick
            treb.destination = None
        treb.target = cible #on met a jour la cible du trebuchet

    def decide(self, engine):
        t = engine.current_time
        if t < self.prochaine_decision:
            return
        self.prochaine_decision = t + self.PERIODE

        parth = engine.get_alive_units("PARTHIAN")
        chateau = engine.castle
        ennemis = parth + ([chateau] if chateau.is_alive() else [])
        if not ennemis:
            return

        if not self.journal:
            self.journal.append("BEDLAM : chaque unité attaque l'ennemi le plus proche")

        for unite in engine.get_alive_units("ROMAN"):
            if isinstance(unite, Trebuchet):
                self._gerer_tribuchet(unite, ennemis, t)
            elif parth:
                # L'ennemi le plus proche (min avec la distance comme critère)
                cible = min(parth, key=unite.distance)
                unite.target = cible
                unite.destination = (cible.x, cible.y)
            else : #plus d'ennemeis on s'arrete de bouger
                unite.target = None
                unite.destination = None