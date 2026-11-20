import pygame
from map import tiles_to_screen, world_to_screen
from constantes import LARGEUR_TILE, LONGUEUR_TILE

class CastleView:
    def __init__(self, castle, sprite_castle):
        self.castle = castle
        self.sprite_castle = sprite_castle
        ratio = sprite_castle.get_height() / sprite_castle.get_width()
        self.largeur_sprite = self.castle.footprint * LARGEUR_TILE
        self.hauteur_sprite = self.largeur_sprite * ratio

    def draw(self, screen, camera_x, camera_y, zoom):

        if self.castle.is_destroyed():
            return  # Ne rien dessiner si le château est détruit
        
        coin_bas_x = self.castle.x + self.castle.footprint
        coin_bas_y = self.castle.y + self.castle.footprint
        monde_x, monde_y = tiles_to_screen(coin_bas_x, coin_bas_y)

        ecran_x, ecran_y = world_to_screen(monde_x, monde_y, camera_x, camera_y, zoom)

        nouvelle_largeur = int(self.largeur_sprite * zoom)
        nouvelle_hauteur = int(self.hauteur_sprite * zoom)

        if nouvelle_largeur <= 0 or nouvelle_hauteur <= 0:
            return  # Ne rien dessiner si la taille est nulle ou négative

        sprite_zomme = pygame.transform.scale(self.sprite_castle, (nouvelle_largeur, nouvelle_hauteur))

        rect = sprite_zomme.get_rect(midbottom=(int(ecran_x), int(ecran_y)))

        screen.blit(sprite_zomme, rect) 