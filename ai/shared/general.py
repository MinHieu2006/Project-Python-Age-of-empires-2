"""Classe de base des généraux (IA)."""


class General:
    """Un général reçoit un Commander (engine/command.py) et donne des
    ordres à son armée. `decide` est appelé toutes les
    `decision_interval` secondes de jeu."""

    name = "General"
    decision_interval = 0.5

    def __init__(self, **params):
        self.params = params

    def setup(self, cmd):
        """Appelé une fois, au premier tour."""

    def decide(self, cmd):
        """Appelé régulièrement pendant la bataille."""

    def __repr__(self):
        args = ", ".join(f"{k}={v}" for k, v in self.params.items())
        return f"{self.name}({args})"
