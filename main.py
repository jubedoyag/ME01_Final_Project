from movimentation_logic import Exploration
from knowledge_base import KnowledgeBase
from environment import *


class Main:

    #Creación del mundo
    world = WumpusWorld()

    #Mostrar mundo creado
    '''for i in range(size):
        print(world.field[i])
    print('\n')
    for i in range(size):
        print(world.perceptions[i])'''
    world.show_world()

    #Establecer KB, exploración y movimiento del agente
    base = KnowledgeBase(world)
    explore = Exploration(world, base)
    explore.move_agent()

    print('\nScore: ' + str(explore.points) + '\n')


if __name__ == '__main__':
    Main()
