import pygame
from constantes import LARGEUR, HAUTEUR, TAILLE_MAP, LARGEUR_TILE, LONGUEUR_TILE , LARGEUR_MAP, LONGUEUR_MAP
from constantes import COULEUR_MINIMAP_FOND, COULEUR_MINIMAP_TERRAIN, COULEUR_MINIMAP_BORDURE, COULEUR_CAMERA, MARGE_MINIMAP, LARGEUR_MINIMAP, HAUTEUR_MINIMAP, ECHELLE_MINIMAP

Zone_Minimap = pygame.Rect(LARGEUR - LARGEUR_MINIMAP - MARGE_MINIMAP, 
                           HAUTEUR - HAUTEUR_MINIMAP - MARGE_MINIMAP, 
                           LARGEUR_MINIMAP +100, 
                           HAUTEUR_MINIMAP+100)  # Zone de la minimap avec une marge de 10 pixels

def map_to_minimap(x, y):
    """Convertit les coordonnées de la carte (Tuile) (colonne, ligne) en coordonnées de la minimap (pixel) (x, y)."""
    minix = Zone_Minimap.x + ( x + LARGEUR_MAP ) * ECHELLE_MINIMAP
    miniy = Zone_Minimap.y + y * ECHELLE_MINIMAP
    return minix, miniy
    

def minimap_to_map(souris_x, souris_y):
    """Empeche la souris de sortir de la zone de la minimap"""
    souris_x=max(Zone_Minimap.left, min(souris_x, Zone_Minimap.right))
    souris_y=max(Zone_Minimap.top, min(souris_y, Zone_Minimap.bottom))
    
    """Opération inverse de monde_vers_minimap : minimap -> monde"""
    map_x = (souris_x - Zone_Minimap.x) / ECHELLE_MINIMAP - LARGEUR_MAP
    map_y = (souris_y - Zone_Minimap.y) / ECHELLE_MINIMAP

    return map_x- LARGEUR / 2, map_y- HAUTEUR / 2

def print_minimap(screen, grille, camera_x, camera_y):

    """Fond de la minimap"""
    pygame.draw.rect(screen, COULEUR_MINIMAP_FOND, Zone_Minimap)

    sommets = [
        map_to_minimap(0, 0),
        map_to_minimap(LARGEUR_MAP , LONGUEUR_MAP ),
        map_to_minimap(0, 2 * LONGUEUR_MAP),
        map_to_minimap(-LARGEUR_MAP, LONGUEUR_MAP)
    ]

    pygame.draw.polygon(screen, COULEUR_MINIMAP_TERRAIN, sommets)
    pygame.draw.polygon(screen, COULEUR_MINIMAP_BORDURE, sommets, 1)


    x, y = map_to_minimap(camera_x, camera_y)
    rect_camera = pygame.Rect(x, y, LARGEUR * ECHELLE_MINIMAP, HAUTEUR * ECHELLE_MINIMAP)
    rect_camera = rect_camera.clip(Zone_Minimap)   # on ne déborde pas de la minimap
    pygame.draw.rect(screen, COULEUR_CAMERA, rect_camera, 1)
