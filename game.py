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

class Field:
    def __init__(self):
        self.board = [[0] * 18 for i in range(5)] # В будущем здесь будут спрайты клеточек
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
                pygame.draw.rect(screen, pygame.Color('white'), (self.left + j * cs, self.top + i * cs, cs, cs), 1)
        for i in range(5):
            for j in range(18):
                if self.board[i][j]:
                    pygame.draw.rect(screen, pygame.Color('white'), (self.left + j * cs, self.top + i * cs, cs, cs), 0)

    def get_cell(self, mouse_pos):
        x, y = mouse_pos
        yo, xo = ceil((x - self.left) / self.cell_size), ceil((y - self.top) / self.cell_size)
        if xo <= 0 or xo > self.height or yo <= 0 or yo > self.width:
            return None, None
        return xo, yo

    def on_click(self, mouse_pos):
        x, y = self.get_cell(mouse_pos)
        x -= 1
        y -= 1
        self.board[x][y] = (self.board[x][y] + 1) % 2

    def get_click(self, mouse_pos):
        self.on_click(mouse_pos)
        return self.get_cell(mouse_pos)


clock = pygame.time.Clock()
fps = 60
run = True
field = Field()
moving = 0
moving_k = 1
while run:
    ticks = 0
    screen.fill(pygame.Color('black'))
    if moving:
        field.left += moving_k * 10
        moving -= 10
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
            if event.unicode == 's':
                field.move()
        if event.type == pygame.MOUSEBUTTONDOWN:
            field.on_click(event.pos)

    field.render(screen)
    all_sprites.draw(screen)
    pygame.display.flip()
    clock.tick(fps)
