import pygame
import numpy
import reinforce.learn as learn
import random
import copy

from hex import Hex

import logging
logging.basicConfig(filename='objects.log', level=logging.DEBUG)


class GameObject:

    def __init__(self, image):
        self.image = pygame.image.load(image).convert_alpha()
        self.pos = Hex(0, 0)
        self.surface = pygame.display.get_surface()
        self.font = pygame.font.SysFont("droidsans", 15)
        self.font.set_bold(True)

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
        x, y = self.pos.pixel_center()
        pygame.display.get_surface().blit(self.image, (
            x + self.width/2, y
        ))

    def draw_text(self, text):
        label = self.font.render(text, 1, (255, 255, 255))
        x, y = self.pos.pixel_center()
        center = x + label.get_rect().width/2
        bottom = y + self.height - label.get_height()
        self.surface.blit(label, (center, bottom))

    def tick(self, curr_ticks):
        self.draw()

    def _set_pos(self, x, y):
        self.pos = Hex(x, y)

    def can_move_to(self, pos):
        return not pos.is_edge()

    def can_move(self, d):

        return self.can_move_to(self.pos + d)

    def move(self, d):
        return self.move_to(self.pos + d)

    def move_to(self, pos):
        if self.can_move_to(pos):
            self.pos = pos


class Container(GameObject):

    def __init__(self, quantity, take_from, place_into):
        self.quantity = quantity
        self.take_from = take_from
        self.place_into = place_into
        image = 'bucket.png' if place_into else 'rocks.png'
        super(Container, self).__init__(image)

    def draw(self):
        super(Container, self).draw()
        self.draw_text("Quantity: {}".format(self.quantity))


class Actor(GameObject):

    def __init__(self, image, objects):
        self.has_rock = False
        self.objects = objects
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

    def pick_up(self):

        if self.has_rock is True:
            return False

        for d in Hex.DIRECTIONS:
            pos = self.pos + d
            for other in self.objects:
                if pos == other.pos and getattr(other, 'take_from', False):
                    self.has_rock = True
                    other.quantity -= 1
                    return True
        return False

    def drop_off(self):

        if self.has_rock is False:
            return False

        for d in Hex.DIRECTIONS:
            pos = self.pos + d
            for other in self.objects:
                if pos == other.pos and getattr(other, 'place_into', False):
                    self.has_rock = False
                    other.quantity += 1
                    return True
        return False


class Avatar(Actor):

    def enqueue_actions(self, actions):
        self.actions = actions

    def tick(self, curr_ticks):
        if (curr_ticks - self.last_tick) >= 100:
            self.last_tick = curr_ticks
            if len(self.actions):
                next_action = self.actions.pop(0)
                if next_action.action == "move":
                    self.move_to(next_action.value)
                elif next_action.action == "pick_up":
                    self.pick_up()
                elif next_action.action == "drop_off":
                    self.drop_off()

        super(Avatar, self).tick(curr_ticks)

    def __init__(self, minions, objects):
        self.actions = []
        self.last_tick = 0
        self.last_move = Hex.DIRECTIONS[0]
        self.minions = minions
        self.observations = {
            True: [],
            False: []
        }
        image = 'necro.png'
        super(Avatar, self).__init__(image, objects)

    def pick_up(self):
        success = super(Avatar, self).pick_up()
        if success:
            state = (self.pos.column, self.pos.row)
            self.observations[False].append([state, self.last_move, 1])
            observations = self.observations[False]
            self.observations[False] = []
            for minion in self.minions:
                last_index = len(minion.observations[True]) - 1
                minion.observations[True].insert(last_index, observations)
        return success

    def drop_off(self):
        success = super(Avatar, self).drop_off()
        if success:
            state = (self.pos.column, self.pos.row)
            self.observations[True].append([state, self.last_move, 1])
            observations = self.observations[True]
            self.observations[True] = []
            for minion in self.minions:
                last_index = len(minion.observations[True]) - 1
                minion.observations[True].insert(last_index, observations)
        return success

    def move(self, d):
        super(Avatar, self).move(d)
        state = (self.pos.column, self.pos.row)
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
        image = 'skeleton.png'
        super(Minion, self).__init__(image, *args, **kwargs)

    def pick_up(self):
        success = super(Minion, self).pick_up()
        if success:
            logging.debug("PICKED UP ROCK")
            logging.debug("TOOK {} MOVES".format(len(self.curr_observations[-1])))
            avg = sum(len(x) for x in self.curr_observations) / len(self.curr_observations)
            std = numpy.std(numpy.array([len(x) for x in self.curr_observations]))
            logging.debug("AVERAGE IS {0:.2f}, STD IS {1:.2f}".format(avg, std))
        return success

    def drop_off(self):
        success = super(Minion, self).drop_off()
        if success:
            logging.debug("DROPPED OFF ROCK")
            logging.debug("TOOK {} MOVES".format(len(self.curr_observations[-1])))
            avg = sum(len(x) for x in self.curr_observations) / len(self.curr_observations)
            std = numpy.std(numpy.array([len(x) for x in self.curr_observations]))
            logging.debug("AVERAGE IS {0:.2f}, STD IS {1:.2f}".format(avg, std))
        return success

    def relearn(self):
        gamma = 0.9
        if len(self.curr_observations) > 1:
            self.models[self.has_rock] = learn(copy.deepcopy(self.curr_observations), gamma)

    def random_dir(self):

        directions = list(Hex.DIRECTIONS)
        random.shuffle(directions)
        for direction in directions:
            if self.can_move(direction):
                return direction

        return False

    def tick(self, curr_ticks):

        if (curr_ticks - self.last_tick) >= 500:
            self.last_tick = curr_ticks
            state = (self.pos.column, self.pos.row)

            if (random.random() < 0.9 and
                    state in self.curr_model and
                    self.can_move(self.curr_model[state])):
                next_direction = self.curr_model[state]
            else:
                next_direction = self.random_dir()

            if next_direction:

                self.move(next_direction)

                if self.drop_off():
                    self.observations[True][-1].append([state, next_direction, 1])
                    self.observations[True].append([])
                elif self.pick_up():
                    self.observations[False][-1].append([state, next_direction, 1])
                    self.observations[False].append([])
                else:
                    self.curr_observations[-1].append([state, next_direction, 0])

                if len(self.curr_observations) % 5 == 0:
                    self.relearn()

        super(Minion, self).tick(curr_ticks)
