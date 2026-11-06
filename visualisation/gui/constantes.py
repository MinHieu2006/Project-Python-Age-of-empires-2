#------------Constantes d'affichage------------#
LARGEUR, HAUTEUR = 1280, 720 # Taille de la fenêtre
LARGEUR_TILE, LONGUEUR_TILE = 64, 32 # Taille d'une tuile
FPS = 60
VITESSE_CAMERA = 2500 # Vitesse de déplacement de la caméra (en pixels par seconde)

ZOOM=1.0  # Facteur de zoom initial
ZOOM_MIN = 0.5  # Facteur de zoom minimum
ZOOM_MAX = 2.0  # Facteur de zoom maximum
VITESSE_ZOOM = 0.1  # Vitesse de zoom (facteur par seconde)


#------------Constantes de la carte------------#
TAILLE_MAP = 120 # Taille de la carte (en nombre de tuiles)
LARGEUR_MAP = TAILLE_MAP * LARGEUR_TILE / 2 # Largeur de la carte en pixels
LONGUEUR_MAP = TAILLE_MAP * LONGUEUR_TILE / 2 # Long

COULEUR_PLAINE = (86, 140, 60)
COULEUR_CONTOUR = (60, 100, 40)
COULEUR_FOND = (0, 0, 0)

#------------Constantes de la minimap------------#
LARGEUR_MINIMAP = 320
HAUTEUR_MINIMAP = 160
MARGE_MINIMAP = 10
ECHELLE_MINIMAP = LARGEUR_MINIMAP / (TAILLE_MAP * LARGEUR_TILE)  # Échelle de la minimap par rapport à la carte soit 1/24

COULEUR_MINIMAP_FOND = (20, 20, 20)
COULEUR_MINIMAP_TERRAIN = (86, 140, 60)
COULEUR_MINIMAP_BORDURE = (200, 200, 200)
COULEUR_CAMERA = (255, 255, 255)

