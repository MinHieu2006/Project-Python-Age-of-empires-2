"""Sargent BRAINDEAD (section 78.1) : les unités ne font rien."""

from ai.shared.general import General


class Braindead(General):
    name = "BRAINDEAD"

    def setup(self, cmd):
        cmd.log("Garde-à-vous. Personne ne bouge.")
