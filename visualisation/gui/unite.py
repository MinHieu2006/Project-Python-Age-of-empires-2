#Pour positioner les trouves sur la carte

import pygame
from map import tiles_to_screen, world_to_screen

# Couleur de chaque type d'unité (le nom de sa classe)
COULEURS = {
    "Legionary": (200, 40, 40),          # rouge
    "Trebuchet": (110, 20, 20),          # rouge foncé
    "Elite_Cataphract": (40, 70, 200),   # bleu
    "Cavalry_Archer": (60, 200, 230),    # bleu clair
}

def dessiner_unite(screen, unite, camera_x, camera_y, zoom=1):
    # Position du sommet de la tuile dans le monde (en pixels)
    monde_x, monde_y = tiles_to_screen(unite.x, unite.y)

    # Conversion vers l'écran avec le zoom et la caméra actifs
    ecran_x, ecran_y = world_to_screen(monde_x, monde_y, camera_x, camera_y, zoom)

    # Rayon adapté au zoom (minimum 2 px pour rester visible en dézoomant fort)
    rayon = max(2, int(8 * zoom))
    epaisseur_contour = max(1, int(2 * zoom))

    # Dessine un cercle représentant l'unité
    couleur = COULEURS.get(type(unite).__name__, (255, 255, 255))
    pygame.draw.circle(screen, couleur, (int(ecran_x), int(ecran_y)), rayon)
    pygame.draw.circle(screen, (0, 0, 0), (int(ecran_x), int(ecran_y)), rayon, epaisseur_contour)