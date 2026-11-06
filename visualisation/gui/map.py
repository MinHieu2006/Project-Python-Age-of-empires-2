#Importation des modules
import pygame
from constantes import LARGEUR, HAUTEUR, LARGEUR_TILE, LONGUEUR_TILE, TAILLE_MAP, COULEUR_PLAINE, COULEUR_CONTOUR
from constantes import ZOOM, ZOOM_MIN, ZOOM_MAX


def creer_map(taille=TAILLE_MAP):
    """Crée une carte vide avec des tuiles."""
    map = [[0 for _ in range (taille)] for _ in range(taille)]
    return map

def tiles_to_screen(colonne, ligne):
    """Convertit les coordonnées de la carte (Tuile) (colonne, ligne) en coordonnées d'écran (pixel) (x, y). """
    """Sachant que la carte est en projection isométrique"""
    x = (colonne - ligne) * LARGEUR_TILE / 2
    y = (colonne + ligne) * LONGUEUR_TILE / 2
    return x, y

def print_map(grille, screen, camera_x , camera_y,zoom):  

    tuile_largeur_zoom = LARGEUR_TILE * zoom
    tuile_hauteur_zoom = LONGUEUR_TILE * zoom
    
    demi_l = tuile_largeur_zoom / 2
    demi_h = tuile_hauteur_zoom / 2

    for ligne in range(len(grille)):
        for colonne in range(len(grille[ligne])):
            x, y = tiles_to_screen(colonne, ligne)

            x  = x * zoom
            y  = y * zoom

            x -= camera_x
            y -= camera_y

            if x + demi_l < 0 or x - demi_l > LARGEUR or y + demi_h < 0 or y - demi_h > HAUTEUR:
                continue  # Ignore les tuiles en dehors de l'écran
            # Les 4 sommets du losange : haut, droite, bas, gauche
            points = [
                (x, y),
                (x + demi_l, y + demi_h),
                (x, y + tuile_hauteur_zoom),
                (x - demi_l, y + demi_h),
            ]   

            #on dessine le polygone représentant la tuile
            
            pygame.draw.polygon(screen, COULEUR_PLAINE, points)            # remplissage
            pygame.draw.polygon(screen, COULEUR_CONTOUR, points, 1)       # contour de 1 pixel
  
