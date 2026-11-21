import math
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

    def stop_at_collision(self, unit, start_x, start_y, destination, units):
        # Displacement from the starting position to the proposed position.
        dx = unit.x - start_x
        dy = unit.y - start_y
        length = dx**2 + dy**2
        if length == 0:
            return

        # Fraction of the proposed movement allowed before the first collision.
        fraction = 1.0
        obstacle = None  # unité qui bloque le mouvement
        for other in units:
            # Ignore the moving unit itself and dead units.
            if other is unit or not other.is_alive():
                continue
            # Vector from the other unit's centre to the starting position.
            offset_x = start_x - other.x
            offset_y = start_y - other.y
            approach = offset_x * dx + offset_y * dy

            # A nonnegative dot product means movement is away or initially tangent.
            if approach >= 0:
                continue

            # Minimum centre-to-centre distance: the sum of both collision radii.
            radius = (unit.unit_collision_radius + other.unit_collision_radius)

            # Squared starting distance minus the squared minimum distance.
            clearance = (offset_x * offset_x + offset_y * offset_y - radius * radius)

            # Positive: separated; zero: touching; negative: overlapping.
            # Stop movement towards a unit that is already touching or overlapping.
            if clearance <= 0:
                fraction = 0
                obstacle = other
                break

            # Solve where the movement line first meets the combined collision circle.
            discriminant = approach * approach - length * clearance
            # A negative discriminant means no intersection; zero means grazing contact.
            if discriminant <= 0:
                continue
            # First contact as a fraction of the proposed movement.
            contact = (-approach - math.sqrt(discriminant)) / length

            # Keep the earliest contact within the movement segment.
            if 0 <= contact <= fraction:
                # Leave a tiny gap to avoid overlap caused by floating-point rounding.
                small_gap = 1e-9 / math.sqrt(length)
                fraction = max(0.0, contact - small_gap)
                obstacle = other
        # Shorten the movement and retain the destination so the unit can retry.
        if fraction < 1.0:
            unit.x = start_x + dx * fraction
            unit.y = start_y + dy * fraction
            unit.destination = destination
            return obstacle
        return None

    def slide_along(self, unit, obstacle, wanted_x, wanted_y, destination, units):
        # Reste du mouvement qui n'a pas pu être fait
        rest_x = wanted_x - unit.x
        rest_y = wanted_y - unit.y
        rest_length = math.hypot(rest_x, rest_y)
        if rest_length < 1e-9:
            return

        # Direction obstacle -> unité (la "normale" au point de contact)
        normal_x = unit.x - obstacle.x
        normal_y = unit.y - obstacle.y
        normal_length = math.hypot(normal_x, normal_y)
        if normal_length < 1e-9:
            return
        normal_x /= normal_length
        normal_y /= normal_length

        # On enlève la partie du mouvement qui rentre dans l'obstacle :
        # il reste la partie qui le longe (la "tangente")
        towards = rest_x * normal_x + rest_y * normal_y
        slide_x = rest_x - towards * normal_x
        slide_y = rest_y - towards * normal_y

        # Si on fonçait droit sur l'obstacle, la tangente est presque nulle :
        # on choisit alors un côté (perpendiculaire à la normale)
        if math.hypot(slide_x, slide_y) < 0.3 * rest_length:
            slide_x = -normal_y * rest_length * 0.5
            slide_y = normal_x * rest_length * 0.5

        # On essaie ce petit déplacement, en vérifiant à nouveau les collisions.
        # Si ce côté est bloqué lui aussi, on essaie l'autre côté.
        start_x, start_y = unit.x, unit.y
        for side in (1, -1):
            unit.x = start_x + side * slide_x
            unit.y = start_y + side * slide_y
            self.stop_at_collision(unit, start_x, start_y, destination, units)
            if math.hypot(unit.x - start_x, unit.y - start_y) > 0.2 * rest_length:
                return  # on a bien avancé : c'est bon
            unit.x, unit.y = start_x, start_y

    def move_units(self, unit, tick_start, units):
        movement_start = max(tick_start, unit.is_attacking_until)

        if isinstance(unit, Trebuchet):
            movement_start = max(movement_start, unit.state_change_end)

        movement_time = self.current_time - movement_start
        if movement_time <= 0:
            return

        # Save the original position and order before proposing movement.
        start_x, start_y = unit.x, unit.y
        destination = unit.destination
        target_x, target_y = destination
        unit.move_towards(target_x, target_y, movement_time, self.current_time)
        
        wanted_x, wanted_y = unit.x, unit.y  # là où l'unité voulait aller
        obstacle = self.stop_at_collision(unit, start_x, start_y, destination, units)
        if obstacle is not None:
            self.slide_along(unit, obstacle, wanted_x, wanted_y, destination, units)

    def resolve_attacks(self, units):
        t = self.current_time
        for unit in units:
            #Un tribuchet doit etre mis à jour a chaque tick pour savoir si il tire ou pas
            if isinstance(unit, Trebuchet):
                shot = unit.update(t)
                if shot is not None:
                    self.shots_this_tick.append(shot)
            target = unit.target
            if target is None or not unit.is_alive():
                continue
            # Cible morte (ou pas une unité) : on oublie la cible
            if not hasattr(target, "is_alive") or not target.is_alive():
                unit.target = None
                continue
            #cas special pour les tribuchets : ils doivent etre deployés pour tirer
            if isinstance(unit, Trebuchet):
                if unit.is_unpacked() and unit.can_attack(t) and unit.is_in_range(target):
                    unit.attack(target, t)
                continue
            if unit.range > 0:
                if unit.distance(target) <= unit.range:
                    unit.attack(target, self.current_time)
            elif hasattr(target, "unit_collision_radius") and unit.is_in_contact(target, tolerance=0.1):
                unit.attack(target, self.current_time)

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
        tick_start = self.current_time
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
        # Move units only after all ongoing trebuchet actions are updated.
        for unit in units_alive:
            if not unit.is_alive() or unit.destination is None:
                continue
            self.move_units(unit, tick_start, units_alive)
        # Update shield wall for Roman Legionaries
        for unit in units_alive:
            if isinstance(unit, Legionary):
                unit.update_shield_wall(self.get_alive_units("ROMAN"))
        self.resolve_attacks(units_alive)
        # Check for game over conditions
        self.check_game_over()
        if self.state == "RUNNING" and self.current_time >= self.time_limit:
            self.state = "DRAW"
        return self.state   
