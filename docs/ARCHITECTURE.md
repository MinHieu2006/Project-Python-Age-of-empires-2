# Architecture

```
scenarios/carrhae.py      Carrhae(...) : construit le monde, lance la bataille, renvoie le résultat
scenarios/batch.py        des centaines de batailles sans affichage, en parallèle
engine/world.py           boucle de simulation : ordres, déplacement, collisions, combat, projectiles
engine/formations/        formations (contrôle de groupe)
engine/command.py         Commander : seule interface entre une IA et le moteur
engine/map/battlefield.py plaine 120x120, château + anneau de falaise, contournement
engine/units/             unités (stats du sujet) ; engine/buildings/castle.py
ai/shared/                General (base), BRAINDEAD, BEDLAM, outils géométriques
ai/roman/crassus.py       IA romaine
ai/parthian/surena.py     IA parthe
visualisation/gui/        vue isométrique pygame, minimap, sprites
```

## Le moteur

* Temps continu par pas de 0.1 s, positions flottantes.
* Chaque unité est un cercle (rayons du sujet). Aucune unité ne peut en
  chevaucher une autre ; pas de poussée, pas d'inertie : les unités se bloquent
  vraiment, ce qui permet de **barrer un passage**.
* Une unité reçoit un ordre individuel (`Order`) : aller à un point (en
  engageant éventuellement les ennemis proches, avec une laisse) ou attaquer
  une cible.
* Attaque : animation (unité immobile), puis coup ou projectile à la fin de
  l'animation ; rechargement compté depuis le début de l'attaque.
* Dégâts : `max(1, Σ max(0, attaque_i - armure_i))`.
* Shield Wall recalculé à chaque pas (10 fois par seconde) à partir des seules
  positions : au moins 4 autres légionnaires à 0.42 ou moins.
* Piétinement : chaque coup de cataphracte touche aussi tous les ennemis dont
  le centre est à 0.75 ou moins du sien.
* Trébuchet : 11 s pour se replier ou se déployer, portée 4–16, précision 80 %
  contre le château, 15 % contre les unités.
* Château : volée de 5 flèches toutes les 2 s, portée 11.

### Choix et écarts à signaler

* **Match nul** : 60 s sans aucun dégât une fois le combat engagé ; avant le
  premier dégât on laisse 180 s, car un trébuchet met environ 90 s à traverser
  la carte. Durée maximale : 30 min.
* Un tir de trébuchet raté tombe à côté sans faire de dégâts.
* Les dégâts d'une flèche sont appliqués à l'impact (flèches à tête chercheuse,
  précision 100 % comme demandé).
* La portée se mesure jusqu'au bord de la cible (bord du château pour le
  trébuchet).

## Les formations

Une `Formation` regroupe des unités et définit :

* une **forme** : `block`, `line` (rangs décalés), `circle` (un ou plusieurs
  anneaux), `wedge` ;
* un **écartement** : serré (0.405, Shield Wall) ou ouvert (1.0–1.1 : rangées
  décalées pour qu'un cavalier de diamètre 0.5 ne passe pas en diagonale) ;
* un **ancrage** (position) et une **orientation**.

À chaque pas, le moteur calcule les places en coordonnées du monde, attribue
une place à chaque unité (au plus proche, avec des échanges locaux quand une
unité est bloquée) et donne à chacune l'ordre d'aller à sa place. L'ancrage
avance à 90 % de la vitesse du plus lent et ralentit si les unités décrochent :
la formation reste cohérente pendant la marche. Les morts sont retirés et les
places recalculées : la formation se reforme seule.

Une formation dense se met d'abord en place en ordre lâche, puis serre les
rangs : un légionnaire ne peut pas se glisser entre deux autres déjà au contact.

Ce qu'une IA peut exprimer :

| Idée du sujet | API |
| --- | --- |
| former un cercle autour d'un point / d'une unité | `circle_around(point_ou_unite, radius)` |
| faire avancer la formation | `move_to(x, y)` |
| se placer entre l'ennemi et une unité | `place_between(protege, menace, distance)` |
| s'étaler / se resserrer | `spread()` / `tighten()` |
| changer de forme | `set_shape(...)` |
| se diviser / fusionner | `split(n)` / `merge(autre)` |
| suivre une unité ou une formation | `follow(cible)` |
| laisser une unité agir seule | `detach(unite, duree)` |

## Les IA

| IA | Camp | Principe |
| --- | --- | --- |
| BRAINDEAD | les deux | ne fait rien |
| BEDLAM | les deux | chaque unité attaque l'ennemi le plus proche |
| CRASSUS | Romains | escorte en anneau infranchissable autour des trébuchets, écran entre trébuchets et cataphractes (dense contre les flèches, ouvert contre le piétinement), tirailleurs en Shield Wall qui repoussent les archers, mêlée à 3 contre 1, personne à portée du château |
| SURENA | Parthes | deux ailes d'archers (appui de la percée / diversion) qui décrochent devant l'infanterie, cataphractes qui cherchent l'angle le moins gardé et chargent par la brèche, frappe d'opportunité sur un trébuchet sans garde, assaut général quand l'infanterie est assez usée |

Paramètres : `Crassus(aggressiveness, screen_distance, cata_alert,
skirmish_groups, skirmish_size)`, `Surena(aggressiveness, kite_distance,
retreat_hp, standoff, max_blockers, assault_ratio)`.

Chaque IA écrit ses décisions dans un journal, affiché dans la vue (touche L)
et renvoyé par `Carrhae`. Les étiquettes de formation (touche F) montrent la
forme, la densité et l'intention courante (CHASSE, REPLI, CHARGE…).
