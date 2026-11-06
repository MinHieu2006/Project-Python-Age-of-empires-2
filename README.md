# FormAItions — Carrhae

Simulateur de bataille 2.5D où deux IA commandent leur armée **en formations**
(projet Python 2026–2027, scénario de Carrhae).

## Installation

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

`pygame-ce` est la version maintenue de pygame (même API, `import pygame`) ; elle
existe pour Python 3.14, contrairement à `pygame`.

## Lancer une bataille

```bash
.venv/bin/python main.py                 # bataille visualisée, Crassus vs Surena
.venv/bin/python -m scenarios.batch 100  # 100 batailles sans affichage, en parallèle
.venv/bin/python -m pytest tests         # tests
```

L'API demandée par le sujet est la fonction `Carrhae` :

```python
from scenarios.carrhae import Carrhae
from ai.roman.crassus import Crassus
from ai.parthian.surena import Surena

r = Carrhae(roman_ai=Crassus(aggressiveness=70), parthian_ai=Surena(),
            n_legionaries=60, n_cataphracts=20, n_cavalry_archers=20,
            n_trebuchets=3, roman_start_position="W", seed=1234,
            map_size=(120, 120), headless=True, speed=1)
print(r.winner, r.reason)      # "ROMAN", "PARTHIAN" ou None (match nul)
r.units                        # état final de chaque unité
r.losses                       # chronologie des pertes
r.decisions                    # journal des décisions de chaque IA
```

## Commandes de la vue

| Touche | Action |
| --- | --- |
| Espace | pause |
| + / - | vitesse (x0.25 à x32) |
| flèches / ZQSD, clic droit glissé | caméra |
| molette | zoom |
| clic sur la minimap | centrer la caméra |
| M | vue globale de la carte |
| F | formations : places, objectif et intention de l'IA |
| H | barres de vie |
| L | journal des décisions |

Les sprites sont dessinés par le programme. Pour utiliser les sprites d'AoE2
(recommandé par le sujet), déposer `legionary.png`, `cataphract.png`,
`cavalry_archer.png`, `trebuchet_packed.png`, `trebuchet_unpacked.png` et
`castle.png` dans `assets/sprites/` : ils sont chargés automatiquement.

## Architecture

Voir [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
