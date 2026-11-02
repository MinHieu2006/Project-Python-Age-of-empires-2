import pygame

#------------Constantes d'affichage------------#
LARGEUR, HAUTEUR = 1280, 720 # Taille de la fenêtre
LARGEUR_TILE, LONGUEUR_TILE = 64, 32 # Taille d'une tuile
FPS = 60
VITESSE_CAMERA = 2500 # Vitesse de déplacement de la caméra (en pixels par seconde)


#------------Couleur de la carte------------#
TAILLE_MAP = 120 # Taille de la carte (en nombre de tuiles)
COULEUR_PLAINE = (86, 140, 60)
COULEUR_CONTOUR = (60, 100, 40)
COULEUR_FOND = (0, 0, 0)

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

def print_map(grille, screen, camera_x , camera_y):  
    
    demi_l = LARGEUR_TILE / 2
    demi_h = LONGUEUR_TILE / 2

    for ligne in range(len(grille)):
        for colonne in range(len(grille[ligne])):
            x, y = tiles_to_screen(colonne, ligne)
            x -= camera_x
            y -= camera_y

            if x + demi_l < 0 or x - demi_l > LARGEUR or y + demi_h < 0 or y - demi_h > HAUTEUR:
                continue  # Ignore les tuiles en dehors de l'écran
            # Les 4 sommets du losange : haut, droite, bas, gauche
            points = [
                (x, y),
                (x + demi_l, y + demi_h),
                (x, y + LONGUEUR_TILE),
                (x - demi_l, y + demi_h),
            ]   

            #on dessine le polygone représentant la tuile
            
            pygame.draw.polygon(screen, COULEUR_PLAINE, points)            # remplissage
            pygame.draw.polygon(screen, COULEUR_CONTOUR, points, 1)       # contour de 1 pixel
  
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