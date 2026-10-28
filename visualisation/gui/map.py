import pygame

#------------Constantes d'affichage------------#
LARGEUR, HAUTEUR = 1280, 720 # Taille de la fenêtre
FPS = 60
COULEUR_FOND = (34, 85, 34)



def main():
    pygame.init()
    screen = pygame.display.set_mode((LARGEUR, HAUTEUR))
    pygame.display.set_caption("Carrhae - Map")
    horloge = pygame.time.Clock()

    running = True
    while running:
        for evenement in pygame.event.get():
            if evenement.type == pygame.QUIT:
                running = False
            elif evenement.type == pygame.KEYDOWN and evenement.key == pygame.K_ESCAPE:
                running = False

        screen.fill(COULEUR_FOND)
        pygame.display.flip()
        horloge.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()