"""Démonstration : une bataille de Carrhae avec visualisation.

    python main.py

Pour changer les paramètres, modifier l'appel ci-dessous (le sujet demande
une API sous forme de fonction, pas de menu ni de ligne de commande)."""

from ai.parthian.surena import Surena
from ai.roman.crassus import Crassus
from scenarios.carrhae import Carrhae

if __name__ == "__main__":
    result = Carrhae(
        roman_ai=Crassus(aggressiveness=50),
        parthian_ai=Surena(aggressiveness=50),
        n_legionaries=60,
        n_cataphracts=20,
        n_cavalry_archers=20,
        n_trebuchets=3,
        roman_start_position="W",
        seed=None,
        map_size=(120, 120),
        headless=False,
        speed=2,
    )
    print(result.summary())
