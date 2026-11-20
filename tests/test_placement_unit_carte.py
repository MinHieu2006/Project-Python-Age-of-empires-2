import os
import sys

Racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, Racine)
sys.path.insert(0, os.path.join(Racine, "visualisation", "gui"))

from main_map import main
from engine.units.legionary import Legionary

if __name__ == "__main__":
    # Créez une liste d'unités pour le test
    unites = [
        Legionary(5, 5), #ici correspond à la position de la tuile sur la carte (colonne, ligne) pas en pixel
        Legionary(10, 10),
        Legionary(15, 15)
    ]
    main(unites=unites)