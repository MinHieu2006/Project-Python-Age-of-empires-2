"""Général romain "Crassus".

Ce que doit faire le général Romain (au minimum) selon le cours selon la section 74 :
- maintenir les trébuchets derrière l’infanterie principale ;
- déployer un large écran pour empêcher les cataphractaires d’atteindre directement le siège ;
- former des groupes compacts lorsque la menace immédiate est constituée par une pluie de flèches ;
- disperser ces groupes à l’approche des cataphractaires ;
- bloquer les axes de passage probables de la cavalerie plutôt que de poursuivre des cavaliers isolés ;
- battre en retraite tout en préservant la géométrie relative de la formation ;
- sacrifier des légionnaires placés en périphérie si cela permet de préserver les trébuchets ;

Le général ne déplace rien lui-même : il remplit seulement
unit.destination (où aller) et unit.target (qui attaquer).
Le moteur (GameEngine) se charge ensuite de faire avancer les unités.
"""

import math

from engine.units.cavalry_archer import Cavalry_Archer
from engine.units.Elite_Cataphract import Elite_Cataphract
from engine.units.legionary import Legionary
from engine.units.trebuchet import Trebuchet


class Crassus:

    nom = "Crassus"

    DISTANCE_DANGER = 3.0         # le légionnaire recule si les cataphractaires sont trop près
    DISTANCE_FUITE = 5.0          # de combien le légionnaire recule
    RAYON_GARDE = 5.0             # rayon pour compter les gardes d'un trébuchet
    DISTANCE_ATTENTE = 14.0       # distance du point d'attente des cataphractaires
    PV_FUITE = 0.3                # sous 30 % de PV
    ENNEMIS_FUITE = 3             # avec 3 cataphractaires collés : on abandonne
    TAILLE_CARTE = 120
    PERIODE = 0.5                 # le général réfléchit toutes les 0.5 s
    DISTANCE_MINIMALE_TREBUCHET = 5.0  # distance minimale entre un trébuchet et un légionnaire

    def __init__(self):
        self.prochaine_decision = 0.0
        self.journal = []
        self.dernier_plan = None