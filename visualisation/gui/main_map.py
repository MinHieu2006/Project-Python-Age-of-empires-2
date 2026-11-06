#Importation des modules
import pygame
from constantes import LARGEUR, HAUTEUR, TAILLE_MAP, FPS, VITESSE_CAMERA, COULEUR_FOND, ZOOM
from  map import creer_map, tiles_to_screen, print_map
from minimap import print_minimap, minimap_to_map, map_to_minimap, Zone_Minimap
from zoom import calcul_zoom




def main():
    pygame.init()
    screen = pygame.display.set_mode((LARGEUR, HAUTEUR))
    pygame.display.set_caption("Carrhae Battle- Map")
    horloge = pygame.time.Clock()
    zoom = ZOOM  # Initialisation du facteur de zoom
    
    grille = creer_map()

    centre_x, centre_y = tiles_to_screen(TAILLE_MAP / 2, TAILLE_MAP / 2)
    camera_x = centre_x - LARGEUR / 2
    camera_y = centre_y - HAUTEUR / 2
    follow_mouse = False

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
                    zoom = calcul_zoom(1, 0.1, zoom)
                
                elif evenement.key == pygame.K_MINUS or evenement.key == pygame.K_KP_MINUS:
                # -1 indique qu'on dézoome (direction = -1)
                    zoom = calcul_zoom(-1, 0.1, zoom)
                 

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
            camera_x, camera_y = minimap_to_map(souris_x, souris_y)
 
        screen.fill(COULEUR_FOND)
        
        print_map(grille, screen, camera_x , camera_y, zoom)  # dessinée en premier : elle est en arrière-plan
        print_minimap(screen, grille, camera_x, camera_y)   # dessinée en dernier : elle passe par-dessus la map
        pygame.display.flip()
        dt = horloge.tick(FPS) / 1000
            
    pygame.quit()


if __name__ == "__main__":
    main()