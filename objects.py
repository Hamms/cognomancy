import pygame
import numpy
import reinforce.learn as learn
import random
import copy

import constants


def random_dir():
    dirs = list(constants.DIRECTIONS.values())
    return random.choice(dirs)


class GameObject:

    def __init__(self, image):
        self.image = pygame.image.load(image).convert_alpha()
        self.pos = self.image.get_rect().move(0, 0)
        self.surface = pygame.display.get_surface()
        self.font = pygame.font.SysFont("droidsans", 15)
        self.font.set_bold(True)

    @property
    def position(self):
        return [c * constants.TILE_SIZE for c in self.pos]

    @property
    def height(self):
        return self.image.get_rect().height

    @property
    def width(self):
        return self.image.get_rect().width

    @property
    def size(self):
        return (self.width, self.height)

    def draw(self):
        pygame.display.get_surface().blit(self.image, self.position)

    def draw_text(self, text):
        label = self.font.render(text, 1, (255,255,255))
        x = self.position[0]
        y = self.position[1]
        self.surface.blit(label, (x + self.width/2 - label.get_rect().width/2, y + self.height))

    def tick(self, curr_ticks):
        self.draw()

    def _set_pos(self, x, y):
        self.pos.left = x
        self.pos.top = y

    def can_move(self, d):

        pos = self.pos.move(*constants.DIRECTIONS[d])

        return (pos.left < constants.MAP_WIDTH and
                pos.left >= 0 and
                pos.top < constants.MAP_HEIGHT and
                pos.top >= 0)

    def move(self, d):

        if self.can_move(d):
            self.pos = self.pos.move(*constants.DIRECTIONS[d])

    def random_dir(self):

        d = random.choice(list(constants.DIRECTIONS.keys()))
        while not self.can_move(d):
            d = random.choice(list(constants.DIRECTIONS.keys()))

        return d


class Container(GameObject):

    def __init__(self, image, quantity):
        self.quantity = quantity
        super(Container, self).__init__(image)

    def draw(self):
        super(Container, self).draw()
        self.draw_text("Quantity: {}".format(self.quantity))


class Actor(GameObject):

    def __init__(self, image, rocks, bucket):
        self.has_rock = False
        self.rocks = rocks
        self.bucket = bucket
        super(Actor, self).__init__(image)

    @property
    def curr_observations(self):
        return self.observations[self.has_rock]

    @property
    def curr_model(self):
        return self.models[self.has_rock]

    def draw(self):
        super(Actor, self).draw()
        if self.has_rock:
            self.draw_text("got rock")

    def can_move(self, d):

        pos = self.pos.move(*constants.DIRECTIONS[d])
        if pos == self.rocks.pos or pos == self.bucket.pos:
            return False

        return super(Actor, self).can_move(d)

    def pick_up(self):

        if self.has_rock is True:
            return False

        for k, v in constants.DIRECTIONS.items():
            pos = self.pos.move(*v)
            if pos == self.rocks.pos:
                self.has_rock = True
                self.rocks.quantity -= 1
                return True
        return False

    def drop_off(self):

        if self.has_rock is False:
            return False

        for k, v in constants.DIRECTIONS.items():
            pos = self.pos.move(*v)
            if pos == self.bucket.pos:
                self.has_rock = False
                self.bucket.quantity += 1
                return True
        return False


class Avatar(Actor):

    def __init__(self, image, rocks, bucket, minions):
        self.last_move = "NORTH"
        self.minions = minions
        self.observations = {
            True: [],
            False: []
        }
        super(Avatar, self).__init__(image, rocks, bucket)

    def pick_up(self):
        success = super(Avatar, self).pick_up()
        if success:
            state = (self.pos.x, self.pos.y)
            self.observations[False].append([state, self.last_move, 1])
            observations = copy.deepcopy(self.observations[False])
            self.observations[False] = []
            for minion in self.minions:
                minion.observations[True].insert(len(minion.observations[True]) - 1, observations)
        return success

    def drop_off(self):
        success = super(Avatar, self).drop_off()
        if success:
            state = (self.pos.x, self.pos.y)
            self.observations[True].append([state, self.last_move, 1])
            observations = copy.deepcopy(self.observations[True])
            self.observations[True] = []
            for minion in self.minions:
                minion.observations[True].insert(len(minion.observations[True]) - 1, observations)
        return success

    def move(self, d):
        super(Avatar, self).move(d)
        state = (self.pos.x, self.pos.y)
        self.curr_observations.append([state, d, 0])


class Minion(Actor):

    def __init__(self, *args, **kwargs):
        self.models = {
            True: dict(),
            False: dict()
        }
        self.observations = {
            True: [[]],
            False: [[]]
        }
        self.last_tick = 0
        super(Minion, self).__init__(*args, **kwargs)

    def pick_up(self):
        success = super(Minion, self).pick_up()
        if success:
            print("PICKED UP ROCK")
            print("TOOK {} MOVES".format(len(self.curr_observations[-1])))
            avg = sum(len(x) for x in self.curr_observations)/len(self.curr_observations)
            std = numpy.std(numpy.array([len(x) for x in self.curr_observations]))
            print("AVERAGE IS {0:.2f}, STD IS {1:.2f}".format(avg, std))
        return success

    def drop_off(self):
        success = super(Minion, self).drop_off()
        if success:
            print("DROPPED OFF ROCK")
            print("TOOK {} MOVES".format(len(self.curr_observations[-1])))
            avg = sum(len(x) for x in self.curr_observations)/len(self.curr_observations)
            std = numpy.std(numpy.array([len(x) for x in self.curr_observations]))
            print("AVERAGE IS {0:.2f}, STD IS {1:.2f}".format(avg, std))
        return success

    def relearn(self):
        gamma = 0.9
        if len(self.curr_observations) > 1:
            self.models[self.has_rock] = learn(copy.deepcopy(self.curr_observations), gamma)

    def tick(self, curr_ticks):
        super(Minion, self).tick(curr_ticks)

        if (curr_ticks - self.last_tick) < 100:
            return

        self.last_tick = curr_ticks
        state = (self.pos.x, self.pos.y)

        if (random.random() < 0.8 and
                (self.pos.x, self.pos.y) in self.curr_model and
                self.can_move(self.curr_model[self.pos.x, self.pos.y])):
            d = self.curr_model[self.pos.x, self.pos.y]
        else:
            d = self.random_dir()

        if self.drop_off():
            self.observations[True][-1].append([state, d, 1])
            self.observations[True].append([])
        elif self.pick_up():
            self.observations[False][-1].append([state, d, 1])
            self.observations[False].append([])
        else:
            self.curr_observations[-1].append([state, d, 0])

        if len(self.curr_observations) % 5 == 0:
            self.relearn()

        self.move(d)

