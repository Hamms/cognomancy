import constants
import random
import math


def random_position():
    x = random.randrange(2, constants.MAP_WIDTH - 2)
    start = -1 * math.floor(x/2)
    y = random.randrange(start + 2, constants.MAP_HEIGHT + start - 2)
    return (x, y)


def random_dir():
    dirs = list(constants.DIRECTIONS.values())
    return random.choice(dirs)
