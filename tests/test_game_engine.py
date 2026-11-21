import unittest

from engine.game_engine import GameEngine
from engine.units.legionary import Legionary

class TestEngine(unittest.TestCase):
    def setUp(self):
        self.engine = GameEngine(time_limit=300.0)
        self.engine.setup_scenario(n_legionaries=60, n_trebuchets=3, n_elite_cataphracts=20, n_cavalry_archers=20)

    def test_initial_setup(self):
        self.assertEqual(len(self.engine.romans), 63)  # 60 Legionaries + 3 Trebuchets
        self.assertEqual(len(self.engine.parthians), 40)  # 20 Elite Cataphracts + 20 Cavalry Archers
        self.assertIsNotNone(self.engine.castle)
        self.assertEqual(self.engine.state, "RUNNING")

    def test_get_alive_units(self):
        alive_romans = self.engine.get_alive_units("ROMAN")
        alive_parthians = self.engine.get_alive_units("PARTHIAN")
        self.assertEqual(len(alive_romans), 63)
        self.assertEqual(len(alive_parthians), 40)

    def test_check_game_over(self):
        # Simulate the castle being destroyed
        self.engine.castle.hp = 0
        self.engine.check_game_over()
        self.assertEqual(self.engine.state, "ROMANS_WIN")
    