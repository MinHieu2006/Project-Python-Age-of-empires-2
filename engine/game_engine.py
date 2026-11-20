from engine.buildings.castle import Castle
from engine.units.legionary import Legionary
from engine.units.trebuchet import Trebuchet
from engine.units.cavalry_archer import Cavalry_Archer
from engine.units.Elite_Cataphract import Elite_Cataphract

class GameEngine:
    def __init__(self, time_limit: float = 300.0):
        # Time management
        self.current_time = 0.0
        self.time_limit = time_limit   # max battle duration in seconds
        self.tick_count = 0

        # Entities in the game
        self.romans = []
        self.parthians = []
        self.castle = None
        self.shots_this_tick = []

        # Game state
        self.state = "RUNNING"  # Possible states: RUNNING, ROMANS_WIN, PARTHIANS_WIN, DRAW

    def setup_scenario(self, n_legionaries: int = 60, n_trebuchets: int = 3, n_elite_cataphracts: int = 20, n_cavalry_archers: int = 20):
        # Initialize the game scenario with specified numbers of units
        self.current_time = 0.0
        self.tick_count = 0
        self.state = "RUNNING"
        self.shots_this_tick.clear()
        # Spawn Castel at the center of the battlefield
        self.castle = Castle(60.0, 60.0)  # Example castle position and health

        # Spawn Roman units at Western corner
        self.romans = []
        for i in range(n_legionaries):
            legionary = Legionary(15.0 + (i % 10) * 0.5, 55.0 + (i // 10) * 0.5, team="ROMAN")
            self.romans.append(legionary)

        # Spawn Trebuchets at Western corner
        for i in range(n_trebuchets):
            trebuchet = Trebuchet(10.0, 58.0 + i * 2.0, team="ROMAN")
            self.romans.append(trebuchet)

        # Spawn Parthian units at Eastern corner
        self.parthians = []
        for i in range(n_elite_cataphracts):
            elite_Cataphract = Elite_Cataphract(45.0 + (i % 5) * 0.8, 55.0 + (i // 5) * 0.8, team="PARTHIAN")
            self.parthians.append(elite_Cataphract)
        for i in range(n_cavalry_archers):
            cavalry_archer = Cavalry_Archer(45.0 + (i % 5) * 0.8, 65.0 + (i // 5) * 0.8, team="PARTHIAN")
            self.parthians.append(cavalry_archer)

    def get_alive_units(self, team: str):
        units = self.romans if team == "ROMAN" else self.parthians
        return [unit for unit in units if unit.is_alive()]

    def check_game_over(self):
        if self.castle and not self.castle.is_alive():
            self.state = "ROMANS_WIN"

        trebs_alive = any(isinstance(u,Trebuchet) and u.is_alive() for u in self.romans)
        if not trebs_alive:
            self.state = "PARTHIANS_WIN"
        return "RUNNING" if self.state == "RUNNING" else self.state

    def step(self, delta_time: float):
        # Advance the game state by delta_time seconds
        if self.castle is None:
            raise RuntimeError("Castle not initialized. Call setup_scenario() first.")
        if self.state != "RUNNING":
            return self.state
        if delta_time <= 0:
            raise ValueError("delta_time must be positive.")
        # Clear shots from the previous tick
        self.shots_this_tick.clear()
        self.current_time += delta_time
        self.tick_count += 1
        units_alive = self.get_alive_units("ROMAN") + self.get_alive_units("PARTHIAN")
        # Update units
        for unit in units_alive:
            if isinstance(unit, Trebuchet):
                # Update trebuchet and check if it fires a shot
                shot = unit.update(self.current_time)
                if shot is not None:
                    self.shots_this_tick.append(shot)
            if not unit.is_alive() or unit.destination is None: 
                continue
            # Move unit towards its destination
            target_x , target_y = unit.destination
            unit.move_towards(target_x, target_y, delta_time, self.current_time)
        # Update shield wall for Roman Legionaries
        for unit in units_alive:
            if isinstance(unit, Legionary):
                unit.update_shield_wall(self.get_alive_units("ROMAN"))
        # Check for game over conditions
        self.check_game_over()
        if self.state == "RUNNING" and self.current_time >= self.time_limit:
            self.state = "DRAW"
        return self.state   
