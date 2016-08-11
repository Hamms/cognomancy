import pygame
import random
import constants

from objects import Container, Avatar, Minion

pygame.init()

surface = pygame.display.set_mode((constants.MAP_WIDTH * constants.TILE_SIZE, constants.MAP_HEIGHT * constants.TILE_SIZE))
background = pygame.image.load('background.jpg').convert()
objects = []
minions = []

rocks = Container('rocks.png', float("inf"))
rocks._set_pos(random.randrange(2, constants.MAP_WIDTH-2), random.randrange(2, constants.MAP_HEIGHT-2))
objects.append(rocks)

bucket = Container('bucket.png', 0)
bucket._set_pos(random.randrange(2, constants.MAP_WIDTH-2), random.randrange(2, constants.MAP_HEIGHT-2))
objects.append(bucket)

avatar = Avatar('necro.png', rocks, bucket, minions)
avatar._set_pos(random.randrange(2, constants.MAP_WIDTH-2), random.randrange(2, constants.MAP_HEIGHT-2))
objects.append(avatar)

for _ in range(3):
    minion = Minion('skeleton.png', rocks, bucket)
    minion._set_pos(random.randrange(2, constants.MAP_WIDTH-2), random.randrange(2, constants.MAP_HEIGHT-2))
    minions.append(minion)
    objects.append(minion)

running = True
while running:

    surface.blit(background, (0, 0))

    for o in objects:
        o.tick(pygame.time.get_ticks())

    pygame.display.update()
    pygame.time.delay(10)

    events = pygame.event.get()
    for event in events:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_w or event.key == pygame.K_UP:
                avatar.move("NORTH")
            elif event.key == pygame.K_s or event.key == pygame.K_DOWN:
                avatar.move("SOUTH")
            elif event.key == pygame.K_d or event.key == pygame.K_RIGHT:
                avatar.move("EAST")
            elif event.key == pygame.K_a or event.key == pygame.K_LEFT:
                avatar.move("WEST")
            elif event.key == pygame.K_SPACE:
                avatar.pick_up()
                avatar.drop_off()
