"""Bataille visuelle entre deux IA, sur la map de main_map.py.

py -m tests.visu_IA                        (IA choisies plus bas)
py -m tests.visu_IA Surena BEDLAMRomain    (IA parthe, puis IA romaine)
py -m tests.visu_IA aucun BEDLAMRomain     ("aucun" = pas d'IA pour ce camp)

Une IA = un fichier ai/parthian/NOM.py (ou ai/roman/NOM.py)
avec une classe NOM qui a une méthode decide(self, engine).
"""
import importlib
import os
import sys

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)
sys.path.insert(0, os.path.join(RACINE, "visualisation", "gui"))

import pygame

from main_map import main
from engine.game_engine import GameEngine
from engine.units.cavalry_archer import Cavalry_Archer

IA_PARTHE = None
IA_ROMAINE = None
PAS = 0.1                       # le moteur avance par pas de 0.1 s


def charger_ia(nom, dossier):
    if nom is None or nom == "aucun":
        return None
    module = importlib.import_module(f"ai.{dossier}.{nom}")   # comme "import ai.dossier.nom"
    return getattr(module, nom)()                              # la classe du même nom


def lancer_attaques(engine, unites):
    """TEMPORAIRE : le moteur ne lit pas encore unit.target, on fait attaquer ici."""
    for unite in unites:
        cible = unite.target
        if cible is None or not hasattr(cible, "is_alive") or not cible.is_alive():
            continue
        if isinstance(unite, Cavalry_Archer) or unite.is_in_contact(cible, tolerance=0.1):
            unite.attack(cible, engine.current_time)


def texte_journal(general):
    if general is None:
        return "pas d'IA"
    journal = getattr(general, "journal", [])
    if not journal:
        return "(vide)"
    ligne = journal[-1]
    if isinstance(ligne, tuple):          # certains journaux notent (temps, texte)
        return f"{ligne[0]} s : {ligne[1]}"
    return str(ligne)


def lancer(nom_parthe=IA_PARTHE, nom_romain=IA_ROMAINE):
    parthe = charger_ia(nom_parthe, "parthian")
    romain = charger_ia(nom_romain, "roman")
    generaux = [g for g in (parthe, romain) if g is not None]   # on enlève les camps sans IA

    engine = GameEngine()
    engine.setup_scenario()
    unites = engine.romans + engine.parthians   # main_map dessine cette liste
    en_retard = [0.0]                           # temps réel pas encore simulé
    police = []                                 # créée une seule fois, à la 1re image

    def mise_a_jour(dt):
        en_retard[0] += dt
        while en_retard[0] >= PAS and engine.state == "RUNNING":
            for general in generaux:
                general.decide(engine)
            engine.step(PAS)
            lancer_attaques(engine, unites)
            en_retard[0] -= PAS
        # On retire les morts de la liste ([:] = on modifie la MÊME liste que main_map)
        unites[:] = [u for u in unites if u.is_alive()]

    def dessiner(screen, camera_x, camera_y, zoom):
        lignes = [
            f"Temps : {engine.current_time:.1f} s   État : {engine.state}",
            f"Parthes ({nom_parthe}) : {len(engine.get_alive_units('PARTHIAN'))} vivants   "
            f"Romains ({nom_romain}) : {len(engine.get_alive_units('ROMAN'))} vivants",
            f"Journal parthe : {texte_journal(parthe)}"[:90],
            f"Journal romain : {texte_journal(romain)}"[:90],
        ]
        if not police:
            police.append(pygame.font.SysFont(None, 24))
        for i, ligne in enumerate(lignes):
            screen.blit(police[0].render(ligne, True, (255, 255, 255)), (10, 10 + i * 22))

    main(unites=unites, mise_a_jour=mise_a_jour, dessiner=dessiner)


if __name__ == "__main__":
    lancer(sys.argv[1] if len(sys.argv) > 1 else IA_PARTHE,
           sys.argv[2] if len(sys.argv) > 2 else IA_ROMAINE)