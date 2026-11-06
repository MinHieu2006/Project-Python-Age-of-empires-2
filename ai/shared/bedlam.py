"""Major BEDLAM (section 78.2) : tout le monde attaque l'ennemi le plus
proche. Aucune tactique, aucune formation."""

from ai.shared.general import General
from engine.constants import TREBUCHET


class Bedlam(General):
    name = "BEDLAM"
    decision_interval = 1.0

    def setup(self, cmd):
        cmd.log("CHARGEZ !")

    def decide(self, cmd):
        enemies = [e for e in cmd.enemy_units()]
        for u in cmd.my_units():
            if u.kind == TREBUCHET:
                if cmd.castle is not None and cmd.castle.is_alive():
                    if u.order is None or u.order.target is not cmd.castle:
                        cmd.attack(u, cmd.castle)
                continue
            target, _ = cmd.nearest(u.x, u.y, enemies)
            if target is None:
                cmd.stop(u)
            elif u.order is None or u.order.target is not target:
                cmd.attack(u, target)
