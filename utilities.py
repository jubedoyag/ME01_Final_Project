from Cryptodome.Random import random


# Retorna todas las posiciones adyacentes al agente, dada su posición actual (arriba,abajo,derecha e izquierda)
def possible_actions(position):
    x, y = position[0], position[1]
    return [[x - 1, y], [x + 1, y], [x, y - 1], [x, y + 1]]


# Exluye las posiciones que corresponden a las paredes en el mundo
def exclude_walls(position, size):

    x, y = position[0], position[1]
    return x > 0 and y > 0 and x < size - 1 and y < size - 1


# Generea un par ordenado de forma aleatoria conforme la dimension de la matriz cuadrada
def random_pair(size):
    x = random.randrange(size)
    y = random.randrange(size)
    return x, y


# Genera todas las posibles combinaciones de un arreglo de booleanos de tamano n
def generate_combinations(n):
    def generate_helper(current_combination, index):
        if index >= n:
            combinations.append(current_combination.copy())
            return

        current_combination[index] = True
        generate_helper(current_combination, index + 1)

        current_combination[index] = False
        generate_helper(current_combination, index + 1)

    combinations = []
    generate_helper([False] * n, 0)
    return combinations
