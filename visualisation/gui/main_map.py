import sys
import os

from visualisation.gui.unite import dessiner_unite

# 1. On indique à Python de remonter de 2 dossiers (pour atteindre la racine du projet)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

#Importation des modules
import pygame
from constantes import LARGEUR, HAUTEUR, TAILLE_MAP, FPS, VITESSE_CAMERA, COULEUR_FOND, ZOOM
from  map import creer_map, tiles_to_screen, print_map, world_to_screen
from minimap import print_minimap, minimap_to_map,Zone_Minimap
from zoom import calcul_zoom
from batiment import CastleView
from engine.buildings.castle import Castle





def main(unites=None):
    pygame.init()
    screen = pygame.display.set_mode((LARGEUR, HAUTEUR))
    pygame.display.set_caption("Carrhae Battle- Map")
    horloge = pygame.time.Clock()
    zoom = ZOOM  # Initialisation du facteur de zoom
    sprite_castle = pygame.image.load("assets/sprites/Castle/castle.png").convert_alpha()
    
    grille = creer_map()

    centre_x, centre_y = tiles_to_screen(TAILLE_MAP / 2, TAILLE_MAP / 2)
    camera_x = centre_x - LARGEUR / 2
    camera_y = centre_y - HAUTEUR / 2
    follow_mouse = False

    tuile_depart_chateau = (TAILLE_MAP / 2) - (Castle.footprint / 2)
    castle = Castle(tuile_depart_chateau, tuile_depart_chateau)
    castle_view = CastleView(castle, sprite_castle)

    dt = 0
    running = True
    while running:
        for evenement in pygame.event.get():
            if evenement.type == pygame.QUIT:
                running = False
            elif evenement.type == pygame.KEYDOWN and evenement.key == pygame.K_ESCAPE:
                running = False
            elif evenement.type == pygame.MOUSEBUTTONDOWN and evenement.button == 1:
                    if Zone_Minimap.collidepoint(evenement.pos):
                        follow_mouse = True
            elif evenement.type == pygame.MOUSEBUTTONUP and evenement.button == 1:
                    follow_mouse = False
            elif evenement.type == pygame.KEYDOWN:
                if evenement.key == pygame.K_PLUS or evenement.key == pygame.K_KP_PLUS:
                # 1 indique qu'on zoome (direction = 1)
                    ancien_zoom = zoom
                    zoom = calcul_zoom(1, 0.1, zoom)
                    camera_x = (camera_x + LARGEUR / 2) * (zoom / ancien_zoom) - LARGEUR / 2
                    camera_y = (camera_y + HAUTEUR / 2) * (zoom / ancien_zoom) - HAUTEUR / 2
                
                elif evenement.key == pygame.K_MINUS or evenement.key == pygame.K_KP_MINUS:
                # -1 indique qu'on dézoome (direction = -1)
                    ancien_zoom = zoom
                    zoom = calcul_zoom(-1, 0.1, zoom)
                    camera_x = (camera_x + LARGEUR / 2) * (zoom / ancien_zoom) - LARGEUR / 2
                    camera_y = (camera_y + HAUTEUR / 2) * (zoom / ancien_zoom) - HAUTEUR / 2

        touches = pygame.key.get_pressed()
        deplacement = VITESSE_CAMERA * dt
        if touches[pygame.K_LEFT]:
            camera_x -= deplacement
        elif touches[pygame.K_RIGHT]:
            camera_x += deplacement
        elif touches[pygame.K_UP]:
            camera_y -= deplacement
        elif touches[pygame.K_DOWN]:
            camera_y += deplacement

        elif follow_mouse == True:
            souris_x, souris_y = pygame.mouse.get_pos()
            camera_x, camera_y = minimap_to_map(souris_x, souris_y, zoom)

        if mise_a_jour is not None:
            mise_a_jour(dt)  # fait avancer ce qu'il y a sur la map (la bataille par exemple)
 
        screen.fill(COULEUR_FOND)
        
        print_map(grille, screen, camera_x , camera_y, zoom)  # dessinée en premier : elle est en arrière-plan
        if dessiner is not None:
            dessiner(screen, camera_x, camera_y, zoom)  # unités, textes... par-dessus de la map
        castle_view.draw(screen, camera_x, camera_y, zoom)  # Dessine le château sur la cartes
        print_minimap(screen, grille, camera_x, camera_y, zoom)   # dessinée en dernier : elle passe par-dessus la map

        #ANTOINE SALE CHIEN, ne suprime pas cette ligne, elle est nécessaire pour le test de placement des unités sur la carte, TROU DU CUL
        for unite in unites:
            dessiner_unite(screen, unite, camera_x, camera_y)  # Dessine les unités sur la carte
        
        pygame.display.flip()
        dt = horloge.tick(FPS) / 1000
            
    pygame.quit()


if __name__ == "__main__":
    main()