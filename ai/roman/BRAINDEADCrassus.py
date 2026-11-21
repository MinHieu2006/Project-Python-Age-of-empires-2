"""Général romain "BRAINDEAD" : il ne fait rien.
"""

class BRAINDEADCrassus:
    
    nom = "BRAINDEAD Crassus"

    def __init__(self):
        self.journal = []

    def decide(self, engine):
        if not self.journal:
            self.journal.append("Je ne fais rien, je suis BRAINDEAD")