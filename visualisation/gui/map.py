import pygame

#------------Constantes d'affichage------------#
LARGEUR, HAUTEUR = 1280, 720 # Taille de la fenêtre
LARGEUR_TILE, LONGUEUR_TILE = 64, 32 # Taille d'une tuile
FPS = 60

#------------Couleur de la carte------------#
TAILLE_MAP = 120 # Taille de la carte (en nombre de tuiles)
COULEUR_FOND = (34, 85, 34)

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

def print_map(map): #reste a faire pour bien afficher chaque tuile sur la carte dans pygame induit modif main notament camera etc etc
    

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