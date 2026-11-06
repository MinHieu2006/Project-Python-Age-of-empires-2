import pygame
import os
import sys
Racine = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, Racine)
sys.path.insert(0, os.path.join(Racine, "engine", "visualisation", "gui"))
from engine.units.legionary import Legionary
from visualisation.gui.map import creer_map
from visualisation.gui.map import tiles_to_screen

def test_main_map_initialization():
    main_map = visualisation.gui.map.creer_map()
    assert main_map is not None
    assert main_map.screen is not None
    assert main_map.grille is not None
    assert main_map.camera_x is not None
    assert main_map.camera_y is not None
    assert main_map.follow_mouse == False

def main2():
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Test Main Map")
    horloge = pygame.time.Clock()

    main_map = visualisation.gui.map.creer_map()

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