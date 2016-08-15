import pygame
import math
from pygame.locals import Color
import constants
black = Color('black')
white = Color('white')

from utils import random_position
from objects import Container, Avatar, Minion
from hex import Hex
from actions import Action

pygame.init()

surface = pygame.display.set_mode((
    int((constants.MAP_WIDTH - 2/3) * Hex.pixel_width() * 3/4),
    int((constants.MAP_HEIGHT - 0.5) * Hex.pixel_height())
))

objects = []
minions = []

rocks = Container(float("inf"), True, False)
rocks._set_pos(*random_position())
objects.append(rocks)

bucket = Container(0, False, True)
bucket._set_pos(*random_position())
objects.append(bucket)

avatar = Avatar(minions, objects)
avatar._set_pos(*random_position())
objects.append(avatar)

for _ in range(3):
    minion = Minion(objects)
    minion._set_pos(*random_position())
    minions.append(minion)
    objects.append(minion)

hexes = []
font = pygame.font.SysFont("droidsans", 15)
font.set_bold(True)
grass = pygame.image.load('grass.png').convert_alpha()
stones = pygame.image.load('stones.png').convert_alpha()
for x in range(constants.MAP_WIDTH):
    start = -1 * math.floor(x/2)
    for y in range(start, constants.MAP_HEIGHT + start):
        hexes.append(Hex(x, y))

for h in hexes:
    print(h.column, h.row, h.to_pixel())
    print(h.row/2 + h.column)

running = True
paused = False
while running:

    for h in hexes:
        img = stones if h.is_edge() else grass
        surface.blit(img, h.pixel_center())

    selected = Hex.pixel_to_hex(*pygame.mouse.get_pos())
    if not selected.is_edge():
        pygame.draw.polygon(surface, white, [selected.corner(i) for i in range(6)], 4)

    for o in objects:
        if paused:
            o.draw()
        else:
            o.tick(pygame.time.get_ticks())

    pygame.display.update()
    pygame.time.delay(10)

    events = pygame.event.get()
    for event in events:
        if event.type == pygame.MOUSEBUTTONUP:

            line = avatar.pos.linedraw(selected)
            actions = [Action("move", h) for h in line[1:]]

            if selected == rocks.pos:
                actions.pop()
                actions.append(Action("pick_up"))
            elif selected == bucket.pos:
                actions.pop()
                actions.append(Action("drop_off"))

            print(actions)
            avatar.enqueue_actions(actions)

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_SPACE:
                paused = not paused
