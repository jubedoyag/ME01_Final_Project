from knowledge_base import KnowledgeBase
from environment import WumpusWorld
from utilities import possible_actions

# Medidas de desempeño propias del wumpus world
got_gold = 1000
got_killed = -1000
action_exe = -1
arrow_use = -10

# Limite de iteraciones sin obtener nuevos conocimientos del entorno
max_iter = 8


class Exploration:

    def __init__(self, world: WumpusWorld, base: KnowledgeBase):

        self.world = world
        self.base = base
        self.position = world.agent
        self.pointing = 'Right'
        self.time = 0
        self.points = 0
        self.gold = False
        self.arrow = True
        self.alive = True

        self.previous_position = world.agent
        self.previous_pointing = 'Right'
        self.wumpus_killed = 0
        self.pits_fallen = 0
        self.arrows_used = 0
        self.total_actions = 0

    def move_agent(self):

        # Primera iteración: Apenas muestra la percepcion recibida por el agente al inicio, y realiza algunos supuestos
        self.previous_position = self.position
        perception = self.world.get_perception(self.position)
        _, count = self.base.tell_perception(self.position, self.previous_position, perception)

        # Si el agente se estanca buscando el oro, la exploración se encierra
        while count < max_iter:

            # Obtiene todas las posiciones adyacentes y pregunta la base de conocimiento (KB) sobre el mejor movimiento a realizar
            actions = possible_actions(self.position)
            next_action = self.base.ask_knowledge_base(self.previous_position, actions)

            # Actualiza las posiciones anteriores y actual del agente
            self.previous_position = self.position
            self.position = next_action

            # Si el agente estuviera en una posicion que contiene un pozo/hueco o el wumpus en sí, el juego se acaba
            self.check_alive(self.position)
            if not self.alive:
                self.points += got_killed
                print('\nThe agent has been killed by the wumpus!')
                break

            # Actualiza la puntuación, dirección anterior y actual del agente
            self.previous_pointing = self.pointing
            actual, self.pointing = self.calculate_action(self.previous_position, self.previous_pointing, self.position)
            self.total_actions += actual

            # Se obtiene la percepción de la posición actual del agente
            perception = self.world.get_perception(self.position)

            # Informa a la base de conocimiento (KB) la percepción actual para inferir los posibles elementos alrededor
            status, count = self.base.tell_perception(self.position, self.previous_position, perception)

            # Si se ecnuentra una pared
            if status == 'Return':
                self.pointing = self.rotate_180(self.previous_pointing)
                self.position = self.previous_position
                self.total_actions += 3     # Gira 180° y mueve hacia adelante
                print('\nThe agent found a WALL and got into position ' + str(self.position))

            # Si se encuentra el otro
            elif status == 'Gold':
                self.total_actions += 1     # Agarrar el oro
                self.points += got_gold
                self.gold = True
                break

            # Si el agente no logra proseguir, este intentará disparar la flecha al wumpus
            if count == max_iter - 1 and self.arrow:
                shoot = self.base.shoot_arrow()

                # Verifica si existe una posición válida para disparar
                if shoot:
                    self.arrow = False
                    self.points += arrow_use
                    check = self.world.kill_wumpus(shoot)
                    self.base.update_knowledge_base(shoot, check)

        # Calcula la puntuación final conforme el numero de acciones ejecutadas
        self.points += self.total_actions * action_exe

    def check_alive(self, position):

        x, y = position[0], position[1]
        perception = self.world.get_perception(position)

        # Menciona si el agente fue muerto conforme la posición dada
        if self.world.field[x][y] == 'P':
            self.alive = False
        elif self.world.field[x][y] == 'W' and perception[4] != 'Scream':
            self.alive = False
        elif self.world.field[x][y] == 'O&W' and perception[4] != 'Scream':
            self.alive = False

    @staticmethod
    def rotate_180(previous_pointing):

        if previous_pointing == 'Right':
            return 'Left'
        elif previous_pointing == 'Left':
            return 'Right'
        elif previous_pointing == 'Up':
            return 'Down'
        else:
            return 'Up'

    @staticmethod
    def calculate_action(previous_position, previous_pointing, position):

        pointing = str()
        actions = 1
        x1, y1 = previous_position[0], previous_position[1]
        x2, y2 = position[0], position[1]

        # X da la posición actual mayor que la anterior (el agente se mueve para abajo)
        if x2 > x1 and y2 == y1:
            pointing = 'Down'

            # Si el agente estaba mirando para arriba, el debe rotar 2 veces para mirar hacia abajo
            if previous_pointing == 'Up':
                actions += 2
            elif previous_pointing == 'Right' or previous_position == 'Left':
                actions += 1

        elif x2 < x1 and y2 == y1:
            pointing = 'Up'

            if previous_pointing == 'Down':
                actions += 2
            elif previous_pointing == 'Right' or previous_position == 'Left':
                actions += 1

        elif x2 == x1 and y2 > y1:
            pointing = 'Right'

            if previous_pointing == 'Left':
                actions += 2
            elif previous_pointing == 'Up' or previous_position == 'Down':
                actions += 1

        elif x2 == x1 and y2 < y1:
            pointing = 'Left'

            if previous_pointing == 'Right':
                actions += 2
            elif previous_pointing == 'Up' or previous_position == 'Down':
                actions += 1

        return actions, pointing
