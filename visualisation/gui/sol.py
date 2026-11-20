import random
import pygame

def charger_sprite_tuile(sprites):

    planche=pygame.image.load(sprites).convert()

    nb_colonnes = 10
    nb_lignes = 10
    largeur_tuile = planche.get_width() // nb_colonnes
    hauteur_tuile = planche.get_height() // nb_lignes

    tuiles = []
    for ligne in range(nb_lignes):
        for colonne in range(nb_colonnes):
            rect = pygame.Rect(colonne * largeur_tuile, ligne * hauteur_tuile, largeur_tuile, hauteur_tuile)
            tuile = planche.subsurface(rect).copy()

            tuiles.set_colorkey((0, 0, 0))  # Définir la couleur noire comme transparente
            tuiles.append(tuile)