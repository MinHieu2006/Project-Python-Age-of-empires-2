"""Lancer beaucoup de batailles sans affichage (en parallèle si possible).

    python -m scenarios.batch            # 100 batailles Crassus vs Surena
    python -m scenarios.batch 20         # 20 batailles
"""

import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor

from scenarios.carrhae import Carrhae


def _one(args):
    roman_cls, roman_kw, parthian_cls, parthian_kw, seed, scenario_kw = args
    r = Carrhae(roman_ai=roman_cls(**roman_kw), parthian_ai=parthian_cls(**parthian_kw),
                seed=seed, headless=True, **scenario_kw)
    return seed, r.winner, r.reason, r.duration


def run_batch(roman_cls, parthian_cls, n=100, roman_kw=None, parthian_kw=None,
              first_seed=0, workers=None, **scenario_kw):
    """Renvoie la liste (seed, vainqueur, raison, durée) et affiche un bilan.
    Les IA sont passées comme classes + paramètres pour pouvoir être
    recréées dans chaque processus."""
    jobs = [(roman_cls, roman_kw or {}, parthian_cls, parthian_kw or {}, s, scenario_kw)
            for s in range(first_seed, first_seed + n)]
    t0 = time.time()
    try:
        with ProcessPoolExecutor(max_workers=workers) as ex:
            results = list(ex.map(_one, jobs))
    except (OSError, PermissionError):
        results = [_one(j) for j in jobs]           # repli séquentiel
    wins = Counter(w or "NUL" for _, w, _, _ in results)
    mean = sum(d for *_, d in results) / max(len(results), 1)
    print(f"{n} batailles en {time.time() - t0:.0f} s | "
          f"Romains {wins['ROMAN']} | Parthes {wins['PARTHIAN']} | nuls {wins['NUL']} | "
          f"durée moyenne {mean:.0f} s de jeu")
    return results


if __name__ == "__main__":
    from ai.parthian.surena import Surena
    from ai.roman.crassus import Crassus
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    run_batch(Crassus, Surena, n)
