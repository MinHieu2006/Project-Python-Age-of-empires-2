import pygame
import os
import sys
Racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, Racine)
sys.path.insert(0, os.path.join(Racine, "engine", "visualisation", "gui"))
from engine.units.legionary import Legionary
from visualisation.gui.main_map import MainMap
from visualisation.gui.main_map import tiles_to_screen

def test_main_map_initialization():
    main_map = visualisation.gui.main_map.MainMap()
    assert main_map is not None
    assert main_map.screen is not None
    assert main_map.grille is not None
    assert main_map.camera_x is not None
    assert main_map.camera_y is not None
    assert main_map.follow_mouse == False

def dessiner_unite(screen, unite, camera_x, camera_y):
    # Dessiner l'unité sur l'écran en tenant compte de la position de la caméra
    x, y = tiles_to_screen(unite.x, unite.y) #position de l'unité sur la carte en pixels
    x -= camera_x
    y -= camera_y
    pygame.draw.circle(screen, (200, 40, 40), (int(x), int(y)), 8)  #le rond
    pygame.draw.circle(screen, (0, 0, 0), (int(x), int(y)), 8, 2)  #le contour du rond

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Test Main Map")
    horloge = pygame.time.Clock()

    main_map = visualisation.gui.main_map.MainMap()

    dt = 0
    running = True
    while running:
        for evenement in pygame.event.get():
            if evenement.type == pygame.QUIT:
                running = False
            elif evenement.type == pygame.KEYDOWN and evenement.key == pygame.K_ESCAPE:
                running = False

        touches = pygame.key.get_pressed()
        deplacement = 200 * dt
        if touches[pygame.K_LEFT]:
            main_map.camera_x -= deplacement
        elif touches[pygame.K_RIGHT]:
            main_map.camera_x += deplacement
        elif touches[pygame.K_UP]:
            main_map.camera_y -= deplacement
        elif touches[pygame.K_DOWN]:
            main_map.camera_y += deplacement

        screen.fill((0, 0, 0))
        main_map.print_map(screen)
        main_map.print_minimap(screen)
        pygame.display.flip()
        dt = horloge.tick(60) / 1000
            
    pygame.quit()