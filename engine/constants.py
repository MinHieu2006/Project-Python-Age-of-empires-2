"""Constantes de la simulation (valeurs du cahier des charges, partie VI)."""

ROMAN = "ROMAN"
PARTHIAN = "PARTHIAN"

# Types d'unités (servent aussi de clés pour les sprites)
LEGIONARY = "legionary"
CATAPHRACT = "cataphract"
CAVALRY_ARCHER = "cavalry_archer"
TREBUCHET = "trebuchet"
CASTLE = "castle"

# Pas de temps de la simulation (secondes de jeu)
DEFAULT_DT = 0.1

# Contact de mêlée : écart maximal entre les deux cercles de collision
MELEE_CONTACT_GAP = 0.05
# À la fin de l'animation, la cible doit encore être à portée de coup
MELEE_RELEASE_GAP = 0.25

# Shield Wall (section 72.3)
SHIELD_WALL_DISTANCE = 0.42
SHIELD_WALL_NEIGHBOURS = 4
SHIELD_WALL_BONUS = 6

# Piétinement du cataphracte (section 72.4) : 0.5 autour de l'unité,
# soit 0.75 depuis son centre
TRAMPLE_RADIUS = 0.75

# Projectiles (purement visuels pour la vitesse, les dégâts tombent à l'impact)
ARROW_SPEED = 9.0
STONE_SPEED = 8.0

# Château (section 72.7)
CASTLE_FOOTPRINT = 4
CLIFF_THICKNESS = 1

# Fin de partie : match nul si plus personne ne fait de dégâts pendant
# DEFAULT_IDLE_TIMEOUT secondes. Avant le premier dégât de la bataille, on
# laisse FIRST_CONTACT_TIMEOUT secondes : sur une carte de 120 cases, un
# trébuchet (0.8 case/s) met environ 90 s à arriver en position de tir.
DEFAULT_IDLE_TIMEOUT = 60.0
FIRST_CONTACT_TIMEOUT = 180.0
DEFAULT_MAX_TIME = 1800.0
