from environment import WumpusWorld
from environment import size
from environment import player_position
from environment import prob
from utilities import possible_actions
from utilities import exclude_walls
from utilities import random
from utilities import generate_combinations


class KnowledgeBase:

    def __init__(self, world: WumpusWorld):

        self.visited = [world.agent]
        self.safe = [world.agent]
        self.limits = list()
        self.danger = list()
        self.unknown = list()

        self.breeze = list()
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
                if [x, y] != player_position and (x != 0 and x != size-1 and y != 0 and y != size-1):
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

        if perception[2] == 'Glitter':
            return 'Gold', self.max_iterations

        if position not in self.safe:
            self.safe.append(position)
            if position in self.possible_pit:
                self.possible_pit.remove(position)
            if position in self.possible_wumpus:
                self.possible_wumpus.remove(position)

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
                    self.no_wumpus.append(adj)
                    self.no_pits.append(adj)

                if perception[0] == 'Stench' and adj not in self.safe and\
                        adj not in self.possible_wumpus and adj not in self.no_wumpus:
                    self.possible_wumpus.append(adj)
                if perception[1] == 'Breeze' and adj not in self.safe and\
                        adj not in self.possible_pit and adj not in self.no_pits:
                    self.possible_pit.append(adj)
                    self.breeze.append(position)

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

        print('Possible pit in:       ' + str(self.possible_pit))
        print('Possible wumpus in:     ' + str(self.possible_wumpus))
        print('Secure positions:       ' + str(self.safe))

        return 'Continue', self.max_iterations

    def use_prob_inference(self, actions):

        print("-- Moving with probabilistic inference")

        # Lista de los cuadrados que son adjacentes a los cuadrados sin hoyos
        frontier = list()

        print("- No pit squares:", self.no_pits)
        for known_square in self.no_pits:
            adjacent = possible_actions(known_square)
            for adj in adjacent:
                if adj not in self.visited:
                    frontier.append(adj)

        # Filtramos los cuadrados en la frontera sin adjacentes con briza (para realizar la operacion de inferencia)
        frontier_with_breezes = list()
        for square in frontier:
            adjacent = possible_actions(square)
            adj_with_breeze = 0
            for adj in adjacent:
                if adj in self.breeze and adj in self.visited:
                    adj_with_breeze += 1
            if adj_with_breeze > 0:
                frontier_with_breezes.append(square)

        # Generamos la distribucion de probabilidad (send helpihna)
        # filtramos las posiciones dentro de la frontera
        # actions_in_frontier = [action for action in actions if action in frontier]
        actions_in_frontier = []
        for action in actions:
            if action in frontier:
                actions_in_frontier.append(action)

        # las posibles combinaciones de booleanos de un arreglo de tamano n
        # representan los modelos posibles (combinaciones de las posiciones) de la frontera
        combinations = generate_combinations(len(frontier)-1)

        # las variables para guardar la posicion con menor prob. de tener un hoyo
        less_prob_p_in_act = 1
        best_action = actions[0]
        # action es el cuadrado que se analizara (query)
        print("- Frontier squares:", frontier)
        print("- Action squares:", actions_in_frontier)
        for action in actions_in_frontier:

            # Primero encontramos el valor de la distrib. de tener un hoyo en action (Pij = True)
            p_in_action = 0
            for combination in combinations:

                filtered_squares = list()
                for i in range(len(combination)):
                    if combination[i]:
                        filtered_squares.append(frontier[i])
                # Como se presupone que hay un hoyo en la posicion actual, lo anadimos a la
                # lista de cuadrados adjacentes a los conocidos y que decimos tienen hoyos.
                filtered_squares.append(action)

                # El modelo de la frontera debe ser consistente con la evidencia (known, Pij = True, frontier)
                is_valid = True

                for breeze_sqr in self.breeze:
                    adjacent = possible_actions(breeze_sqr)

                    has_adjacents = 0
                    for adj in adjacent:
                        # Esto significa que el cuadrado que tiene un hoyo es adjacente al que tiene brisa
                        if adj in filtered_squares:
                            has_adjacents += 1
                    is_valid = is_valid and (has_adjacents > 0)

                frontier_model_value = 1
                if is_valid:
                    for square_have_pit in combination:
                        frontier_model_value *= prob if square_have_pit else (1 - prob)
                else:
                    frontier_model_value = 0

                p_in_action += frontier_model_value

            p_in_act_value = p_in_action * prob

            # Luego encontramos el valor de la distrib. al NO tener un hoyo en action (Pij = False)
            no_p_in_action = 0
            for combination in combinations:

                filtered_squares = list()
                for i in range(len(combination)):
                    if combination[i]:
                        filtered_squares.append(frontier[i])
                # En este caso no hay hoyo en la posicion actual, por lo que no se agrega

                # El modelo de la frontera debe ser consistente con la evidencia (known, Pij = False, frontier)
                is_valid = True

                for breeze_sqr in self.breeze:
                    adjacent = possible_actions(breeze_sqr)

                    has_adjacents = 0
                    for adj in adjacent:
                        # Esto significa que el cuadrado que tiene un hoyo es adjacente al que tiene brisa
                        if adj in filtered_squares:
                            has_adjacents += 1
                    is_valid = is_valid and (has_adjacents > 0)

                frontier_model_value = 1
                if is_valid:
                    for square_have_pit in combination:
                        frontier_model_value *= prob if square_have_pit else (1 - prob)
                else:
                    frontier_model_value = 0

                no_p_in_action += frontier_model_value

            no_p_in_act_value = no_p_in_action * (1 - prob)

            # Encontramos la normalizacion de los valores p y ¬p para la distribucion, esto
            # es, encontrar las probabilidades de ambos casos: posicion con y sin hoyo
            alpha = p_in_act_value + no_p_in_act_value
            p_prob = p_in_act_value / alpha

            # Si la probabilidad de que esta posicion (action) tenga un hoyo es menor,
            # se deja como la mejor opcion
            print("- Action:", action, " - Pit Prob.:", str(p_prob)[:6])
            if p_prob < less_prob_p_in_act:
                print("- Chosen action:", action)
                less_prob_p_in_act = p_prob
                best_action = action

        print("-- Moving to:", best_action)
        return best_action

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

            if previous_position in prior_1 and len(prior_1) == 1:
                # En caso de no contar con posiciones seguras, se movera a la que posea menor probabilidad de hoyo
                next_action = self.use_prob_inference(actions)
                return next_action

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
            print('\nThe agent shot the arrow toward ' + str(shoot) + ' and killed the wumpus!')

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

            print('\nThe agent shot the arrow toward ' + str(shoot) + ' and did not kill the wumpus!')

        # Continua la exporación
        self.max_iterations = 0
