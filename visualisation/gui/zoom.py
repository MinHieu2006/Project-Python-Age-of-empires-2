import pygame
import sys
from constantes import ZOOM_MIN, ZOOM_MAX

def calcul_zoom(direction, VITESSE_ZOOM, ZOOM_ACTUEL):
    # direction sera 1 (pour zoomer) ou -1 (pour dézoomer)
    ZOOM_ACTUEL += direction * VITESSE_ZOOM
    ZOOM_ACTUEL = max(ZOOM_MIN, min(ZOOM_MAX, ZOOM_ACTUEL))  # Limite le zoom
    return ZOOM_ACTUEL

def new_largeur_hauteur(LARGEUR, HAUTEUR, ZOOM):
    """Calcule la nouvelle largeur et hauteur en fonction du facteur de zoom."""
    new_largeur = int(LARGEUR * ZOOM) 
    new_hauteur = int(HAUTEUR * ZOOM) 
    return new_largeur, new_hauteur