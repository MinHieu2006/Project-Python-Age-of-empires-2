#Importation des modules
import pygame
from constantes import LARGEUR, HAUTEUR, TAILLE_MAP, FPS, VITESSE_CAMERA, COULEUR_FOND
from  map import creer_map, tiles_to_screen, print_map



def main():
    pygame.init()
    screen = pygame.display.set_mode((LARGEUR, HAUTEUR))
    pygame.display.set_caption("Carrhae Battle- Map")
    horloge = pygame.time.Clock()

    grille = creer_map()

    centre_x, centre_y = tiles_to_screen(TAILLE_MAP / 2, TAILLE_MAP / 2)
    camera_x = centre_x - LARGEUR / 2
    camera_y = centre_y - HAUTEUR / 2

    dt = 0
    running = True
    while running:
        for evenement in pygame.event.get():
            if evenement.type == pygame.QUIT:
                running = False
            elif evenement.type == pygame.KEYDOWN and evenement.key == pygame.K_ESCAPE:
                running = False

        touches = pygame.key.get_pressed()
        deplacement = VITESSE_CAMERA * dt
        if touches[pygame.K_LEFT]:
            camera_x -= deplacement
        if touches[pygame.K_RIGHT]:
            camera_x += deplacement
        if touches[pygame.K_UP]:
            camera_y -= deplacement
        if touches[pygame.K_DOWN]:
            camera_y += deplacement

        screen.fill(COULEUR_FOND)
        print_map(grille, screen, camera_x, camera_y)
        pygame.display.flip()
        dt = horloge.tick(FPS) / 1000 # Convertit le temps écoulé de secondesen secondes
    
    pygame.quit()


if __name__ == "__main__":
    main()