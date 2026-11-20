from engine.game_engine import GameEngine
from ai.parthian.BRAINDEADSurena import BRAINDEADSurena

# On crée la partie avec les effectifs du sujet
engine = GameEngine(time_limit=60)
engine.setup_scenario(n_legionaries=60, n_trebuchets=3,
                      n_elite_cataphracts=20, n_cavalry_archers=20)

# On crée le général parthe
general = BRAINDEADSurena()
print("Général parthe :", general.nom)

# On retient où sont les Parthes au début
positions_depart = [(u.x, u.y) for u in engine.parthians]

# On joue : à chaque tick, le général décide, puis le moteur avance de 0.1 s
while engine.state == "RUNNING":
    general.decide(engine)
    engine.step(0.1)

# On vérifie le résultat
print("Résultat :", engine.state, "après", round(engine.current_time), "secondes")
print("Parthes vivants :", len(engine.get_alive_units("PARTHIAN")), "/", len(engine.parthians))
print("Romains vivants :", len(engine.get_alive_units("ROMAN")), "/", len(engine.romans))

nb_ordres = sum(1 for u in engine.parthians if u.destination is not None or u.target is not None)
print("Unités parthes avec un ordre :", nb_ordres)

nb_deplacees = sum(1 for u, (x, y) in zip(engine.parthians, positions_depart)
                   if (u.x, u.y) != (x, y))
print("Unités parthes qui ont bougé :", nb_deplacees)

print("Lignes dans le journal :", len(general.journal))
print("Première ligne :", general.journal[0])
