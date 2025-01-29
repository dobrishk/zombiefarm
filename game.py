import os
import sys
import copy
import random
from math import ceil

import pygame

pygame.init()

WIDTH, HEIGHT = 800, 600

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Zombie Farm")


def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        print(f'Файл с изображением {fullname} не найден.')
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image


all_sprites = pygame.sprite.Group()


class Ruler:
    def __init__(self, view):
        self.cell_size = 70
        if view == 1:
            self.size = 3
            self.board = ['white', 'blue', 'red']
            self.left = 170
            self.top = 5
        else:
            self.size = 5
            self.board = ['red', 'yellow', 'green', 'blue', 'purple']
            self.left = 1080
            self.top = 5

    def render(self, screen):
        for i in range(self.size):
            pygame.draw.rect(screen, pygame.Color(self.board[i]),
                             (self.left + i * self.cell_size, self.top, self.cell_size, self.cell_size), 0)

    def get_cell(self, mouse_pos):
        x, y = mouse_pos
        yo, xo = ceil((x - self.left) / self.cell_size), ceil((y - self.top) / self.cell_size)
        if xo <= 0 or xo > 1 or yo <= 0 or yo > self.size:
            return None, None
        return xo, yo

    def on_click(self, mouse_pos):
        global picked_plant, picked_i
        x, y = self.get_cell(mouse_pos)
        if x == None:
            return
        x -= 1
        y -= 1
        picked_plant = self.board[y]
        if self.left < ruler_r.left:
            picked_i = (1, y)
        else:
            picked_i = (2, y)

    def get_click(self, mouse_pos):
        self.on_click(mouse_pos)
        return self.get_cell(mouse_pos)

    def unpick(self):
        global picked_plant, picked_i
        if picked_i[0] == 1:
            ruler_l.board[picked_i[1]] = picked_plant
        else:
            ruler_r.board[picked_i[1]] = picked_plant
        picked_i = tuple()
        picked_plant = ''


class Cell:
    def __init__(self):
        self.disabled = 0
        self.num = 0

        self.temp_color = 'black'

    def set(self):
        global picked_plant
        # if self.disabled == 0 and picked_plant and self.num == 0:
        #     self.num = picked_plant
        # picked_plant = 0

        if self.disabled == 0 and picked_plant and self.num == 0:
            self.num = picked_plant
            ruler_l.unpick()

        self.disabled = 20

    def draw(self, pos):
        # col = pygame.Color('black')
        # if self.num == 1:
        #     col = pygame.Color('white')
        # elif self.num == 2:
        #     col = pygame.Color('orange')

        col = self.temp_color

        pygame.draw.rect(screen, col, pos, 0)
        self.disabled = max(0, self.disabled - 1)


class Field:
    def __init__(self):
        self.board = [[Cell() for i in range(18)] for i in range(5)]
        self.height = 5
        self.width = 18
        self.cell_size = 70
        self.left = 170
        self.top = 175

    def move(self):
        global moving, moving_k
        if self.left > 0:
            moving = 800
            moving_k = -1
        else:
            moving = 800
            moving_k = 1

    def render(self, screen):
        cs = self.cell_size
        for i in range(5):
            for j in range(18):
                self.board[i][j].draw((self.left + j * cs, self.top + i * cs, cs, cs))
        for i in range(5):
            for j in range(18):
                pygame.draw.rect(screen, pygame.Color('white'), (self.left + j * cs, self.top + i * cs, cs, cs), 1)

    def get_cell(self, mouse_pos):
        x, y = mouse_pos
        yo, xo = ceil((x - self.left) / self.cell_size), ceil((y - self.top) / self.cell_size)
        if xo <= 0 or xo > self.height or yo <= 0 or yo > self.width:
            return None, None
        return xo, yo

    def on_click(self, mouse_pos):
        x, y = self.get_cell(mouse_pos)
        if x == None:
            return
        x -= 1
        y -= 1
        self.board[x][y].set()

    def get_click(self, mouse_pos):
        self.on_click(mouse_pos)
        return self.get_cell(mouse_pos)


clock = pygame.time.Clock()
fps = 60
run = True
field = Field()
ruler_l = Ruler(1)
ruler_r = Ruler(2)
moving = 0
moving_k = 1
picked_plant = ''
picked_i = tuple()
while run:
    ticks = 0
    screen.fill(pygame.Color('black'))
    if moving:
        field.left += moving_k * 10
        ruler_l.left += moving_k * 10
        ruler_r.left += moving_k * 10
        moving -= 10
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
            if event.unicode == 's':
                field.move()
            if event.unicode == 'z':
                picked_plant = 1
            if event.unicode == 'x':
                picked_plant = 2
        if event.type == pygame.MOUSEBUTTONDOWN:
            field.on_click(event.pos)
            ruler_l.on_click(event.pos)
            ruler_r.on_click(event.pos)

    field.render(screen)
    ruler_l.render(screen)
    ruler_r.render(screen)
    all_sprites.draw(screen)
    pygame.display.flip()
    clock.tick(fps)
