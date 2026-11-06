import pygame
from map import tiles_to_screen

def dessiner_unite(screen, unite, camera_x, camera_y):
    # Dessiner l'unité sur l'écran en tenant compte de la position de la caméra
    x, y = tiles_to_screen(unite.x, unite.y) #position de l'unité sur la carte en pixels
    x -= camera_x
    y -= camera_y
    pygame.draw.circle(screen, (200, 40, 40), (int(x), int(y)), 8)  #le rond
    pygame.draw.circle(screen, (0, 0, 0), (int(x), int(y)), 8, 2)  #le contour du rond