from environment import WumpusWorld
from environment import size
from environment import player_position
from utilities import possible_actions
from utilities import exclude_walls
from utilities import random


class KnowledgeBase:

    def __init__(self, world: WumpusWorld):

        self.visited = [world.agent]
        self.safe = [world.agent]
        self.limits = list()
        self.danger = list()
        self.unknown = list()

        self.possible_pit = list()
        self.possible_wumpus = list()
        self.no_pits = list()
        self.no_wumpus = list()
        self.max_iterations = 0

        self.get_unknown_positions()

    def get_unknown_positions(self):

        positions = list()

        # Obtiene todads las posiciones del mundo, excepto la que el agente empieza
        for x in range(size):
            for y in range(size):
                if [x, y] != player_position:
                    positions.append([x, y])

        self.unknown = positions.copy()

    def tell_perception(self, position, previous_position, perception):

        # Si la posición actual es visitada por primera vez, se adiciona a la lista de visitados y reinicia el contador para continuar la exploración
        if position not in self.visited:
            self.max_iterations = 0
            self.visited.append(position)
        else:
            self.max_iterations += 1

        # Si la posición actual era desconocida, obviamente es conocida en este momento
        if position in self.unknown:
            self.unknown.remove(position)

        print('\n')
        print('Current position:          ' + str(position))
        print('Current percept:        ' + str(perception))
        print('Unknown positions: ' + str(self.unknown))

        # Si el agente camina para una pared, este recibe una percepción de impacto e debe volver para su posición anterior
        if perception[3] == 'Bump':
            self.limits.append(position)
            return 'Return', self.max_iterations

        if perception[2] == 'Repudiation':
            return 'Data', self.max_iterations

        if position not in self.safe:
            self.safe.append(position)

        # Obtiene todos los adyacentes de la posición actual, excluyendo la anterior
        adjacent = possible_actions(position)
        if position != previous_position:
            adjacent.remove(previous_position)

        # Si la percepción actual indica cierto peligro, las posiciones adyacentes son marcadas indicando los lugares donde el agente no podria arriesgarse a ir
        for adj in adjacent:

            # Analiza solamente posiciones interiores al mundo (excluyendo las paredes)
            if exclude_walls(adj, size):
                # Si no hay brisa o hedor, las posciones adyacentes son seguras
                if perception[0] == 'Nothing' and perception[1] == 'Nothing' and adj not in self.safe:
                    self.safe.append(adj)

                if perception[0] == 'Noise' and adj not in self.safe and\
                        adj not in self.possible_wumpus and adj not in self.no_wumpus:
                    self.possible_wumpus.append(adj)
                if perception[1] == 'Bait' and adj not in self.safe and\
                        adj not in self.possible_pit and adj not in self.no_pits:
                    self.possible_pit.append(adj)

                # El agente puede descartar posibles Wumpus y Pits en determinadas posiciones de acuerdo con las percepciones anteriores
                if perception[0] == 'Nothing' and adj in self.possible_wumpus:
                    self.no_wumpus.append(adj)
                if perception[1] == 'Nothing' and adj in self.possible_pit:
                    self.no_pits.append(adj)

        for x in self.no_wumpus:
            if x in self.possible_wumpus:
                self.possible_wumpus.remove(x)

        for x in self.no_pits:
            if x in self.possible_pit:
                self.possible_pit.remove(x)

        print('Possible Honeypot in:       ' + str(self.possible_pit))
        print('Possible IDS in:     ' + str(self.possible_wumpus))
        print('Vulnerable positions:       ' + str(self.safe))

        return 'Continue', self.max_iterations

    def ask_knowledge_base(self, previous_position, actions):

        prior_1, prior_2, prior_3 = list(), list(), list()

        # Posibilita al agente caminar para una pared, recibiendo así un impacto en la percepcion
        # Retorna una accion que garante la seguridad del agente, priorizando por posiciones desconocidas en el mundo
        for action in actions:
            if action in self.unknown and action not in self.possible_wumpus and action not in self.possible_pit:
                prior_3.append(action)

        if prior_3:
            if previous_position in prior_3 and len(prior_3) > 1:
                prior_3.remove(previous_position)
            return random.choice(prior_3)

        # Busca por posiciones seguras, pero no visitadas
        for action in actions:
            if action in self.safe and action not in self.visited:
                prior_2.append(action)

        if prior_2:
            if previous_position in prior_2 and len(prior_2) > 1:
                prior_2.remove(previous_position)
            return random.choice(prior_2)

        # Retorna una posicion segura y ya visitada, en caso negativo en las dos condiciones anteriores
        for action in actions:
            if action in self.safe:
                prior_1.append(action)

        if prior_1:
            if previous_position in prior_1 and len(prior_1) > 1:
                prior_1.remove(previous_position)
            return random.choice(prior_1)

    def shoot_arrow(self):

        # Si existen posiciones válidas en que el Wumpus puede estar
        if self.possible_wumpus:

            # SI existen mas de una, el agente escoge de forma aleatoria para donde disparar
            if len(self.possible_wumpus) > 1:
                return random.choice(self.possible_wumpus)

            # Tiro certero
            else:
                return self.possible_wumpus[0]
        else:
            return False

    def update_knowledge_base(self, shoot, check):

        # Si el wumpus murió o no, se actualiza la base de conocimientos
        if check:
            print('\nThe Malware tried to bypass ' + str(shoot) + ' and has deactivated the IDS!')

            self.safe.append(shoot)
            self.possible_wumpus.remove(shoot)

            if self.possible_wumpus:
                for position in self.possible_wumpus:
                    if position not in self.possible_pit:
                        self.possible_wumpus.pop(0)
                        self.safe.append(position)
        else:
            if shoot not in self.possible_pit:
                self.possible_wumpus.remove(shoot)
                self.safe.append(shoot)

            print('\nThe Malware tried to bypass  ' + str(shoot) + ' and has not deactivated the IDS')

        # Continua la exporación
        self.max_iterations = 0
