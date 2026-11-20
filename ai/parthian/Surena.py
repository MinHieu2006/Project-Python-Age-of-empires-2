"""Général parthe "Surena".

Idée générale selon la section 75 du sujet :
- des archers à cheval tire sur les légionnaires
  pour les attirer loin des trébuchets, et recule dès qu'un légionnaire
  s'approche ;
- d'autres archers contourne la légion et tire sur les trébuchets
  depuis le côté le moins gardé ;
- les cataphractes attendent à l'écart et ne chargent que le trébuchet
  le moins protégé ;
- une unité trop blessée et entourée abandonne le combat.

Le général ne déplace rien lui-même : il remplit seulement
unit.destination (où aller) et unit.target (qui attaquer).
Le moteur (GameEngine) se charge ensuite de faire avancer les unités.
"""

import math

from engine.units.cavalry_archer import Cavalry_Archer
from engine.units.Elite_Cataphract import Elite_Cataphract
from engine.units.legionary import Legionary
from engine.units.trebuchet import Trebuchet


class Surena:

    nom = "Surena"

    DISTANCE_DANGER = 3.0         # l'archer recule si les légionnaires sont trop près
    DISTANCE_FUITE = 5.0          # de combien l'archer recule
    RAYON_GARDE = 5.0             # rayon pour compter les gardes d'un trébuchet
    DISTANCE_ATTENTE = 14.0       # distance du point d'attente des cataphractes
    PV_FUITE = 0.3                # sous 30 % de PV
    ENNEMIS_FUITE = 3             # avec 3 légionnaires collés : on abandonne
    TAILLE_CARTE = 120
    PERIODE = 0.5                 # le général réfléchit toutes les 0.5 s

    def __init__(self):
        self.prochaine_decision = 0.0
        self.journal = []
        self.dernier_plan = None