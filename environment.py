from utilities import random_pair


# Dimensipon de la matriz
# 6 -> matriz 4x4, las filas y columnas 0 y 5, corresponden apenas a las paredes del mundo como limites
size = 6

# Probabilidad de una posicion cualquiera del mundo (excepto la inicial) de ser un Pit
prob = 0.2

# Posición inicial del agente
player_position = [size - 2, 1]

# Posiciones adyacentes al jugador en que no pueden ser posicionados Pits y el Wumpus
adj1 = [size - 3, 1]
adj2 = [size - 2, 2]


class WumpusWorld:

    def __init__(self):

        self.field = [['-'] * size for i in range(size)]
        self.limits = [['X'] * size for i in range(size)]
        self.agent = [size - 2, 1]
        self.perceptions = None

        self.place_limits()
        self.place_agent()
        self.place_gold()
        self.place_wumpus()
        self.place_pits()
        self.perceptions_build()

    # El agente siempre es colocado en la misma posición (Esquina inferior izquierda del mundo)
    def place_agent(self):

        self.field[size - 2][1] = 'R'

    # Posiciona el oro en el mundo de forma aleatoria
    def place_gold(self):
        while True:
            x, y = random_pair(size)
            if self.field[x][y] == '-' and self.limits[x][y] != 'Wall':
                self.field[x][y] = 'D'
                break

    # Posiciona el Wumpus en el mundo de forma aleatoria
    def place_wumpus(self):
        while True:
            x, y = random_pair(size)
            if self.field[x][y] == '-' and self.limits[x][y] != 'Wall' and [x, y] != adj1 \
                    and [x, y] != adj2:
                if self.field[x][y] == '-':
                    self.field[x][y] = 'I'
                else:
                    self.field[x][y] = 'D&I'  # oro y Wumpus en la misma posicion
                break

    # Posiciona los Pits en el mundo de forma aleatoria, con probabilidad del 20% para el total de posiciones
    def place_pits(self):
        n_pits = int((pow(size - 2, 2) - 1) * prob)

        i = 0
        while i < n_pits:
            x, y = random_pair(size)

            if self.field[x][y] == '-' and [x, y] != adj1 and [x, y] != adj2 and self.limits[x][y] != 'Wall':
                self.field[x][y] = 'H'
                i += 1

    # Delimitación de los limites
    def place_limits(self):

        for x in range(size):
            for y in range(size):
                if (x == 0) or (y == 0) or (x == size - 1) or (y == size - 1):
                    self.limits[x][y] = 'Wall'
                    self.field[x][y] = 'X'

    # Revisa si existen posiciones válidas (que no son paredes) arriba, abajo, izquierda y a la derecha de la posición dada, respectivamente
    def adjacent(self, x, y):

        adjacents = list()

        if x - 1 > 0:
            adjacents.append(self.field[x - 1][y])
        else:
            adjacents.append('Nothing')

        if x + 1 < size - 1:
            adjacents.append(self.field[x + 1][y])
        else:
            adjacents.append('Nothing')

        if y - 1 > 0:
            adjacents.append(self.field[x][y - 1])
        else:
            adjacents.append('Nothing')

        if y + 1 < size - 1:
            adjacents.append(self.field[x][y + 1])
        else:
            adjacents.append('Nothing')

        return adjacents

    def perceptions_build(self):
        field = list()
        # Adiciona las percepciones de cada posición del mundo conforme el posicionamente de los objetos
        for x in range(size):
            perception_line = list()
            for y in range(size):
                perception = ['Nothing', 'Nothing', 'Nothing', 'Nothing', 'Nothing']
                neighbors = self.adjacent(x, y)
                if self.limits[x][y] == 'Wall':
                    perception[3] = 'Bump'
                else:
                    if 'I' in neighbors:
                        perception[0] = 'Noise'
                    #if 'D&I' in neighbors:
                    #    perception[0] = 'Noise'
                    if 'H' in neighbors:
                        perception[1] = 'Bait'
                    if self.field[x][y] == 'D' or self.field[x][y] == 'D&I':
                        perception[2] = 'Repudiation'
                perception_line.append(perception)
            field.append(perception_line)
        self.perceptions = field

    def kill_wumpus(self, position):
        x, y = position[0], position[1]
        # Si el agente dispara la flecha en la posición donde está el Wumpus, su grito se envia a todas las percepciones del ambiente
        if self.field[x][y] == 'I' or self.field[x][y] == 'D&I':
            for i in range(size - 1):
                for j in range(size - 1):
                    self.perceptions[i][j][4] = 'Blackout'
                    # Si el Wumpus es muerto, su hedor deja de existis en el ambiente
                    if self.perceptions[i][j][0] == 'Noise':
                        self.perceptions[i][j][0] = 'Nothing'

            return True

        return False

    def get_perception(self, position):
        x = position[0]
        y = position[1]
        return self.perceptions[x][y]

    #---------------------- Utilities ----------------------
    def show_world(self):
        print("\n")
        for i in range(size):
            print(" ".join(self.field[i]))
