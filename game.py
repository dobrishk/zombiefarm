import os
import sys
import random
import json
from math import ceil
import pygame

pygame.init()
pygame.mixer.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Защити рассаду!")


def resize_image(img, size=(70, 70)):
    return pygame.transform.scale(img, size)


def load_image(name, colorkey=None):
    fullname = os.path.join("data", name)
    if not os.path.isfile(fullname):
        print(f"Файл {fullname} не найден.")
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


pygame.mixer.music.load(os.path.join("data", "background_music.mp3"))
pygame.mixer.music.play(-1)
sfx_plant = pygame.mixer.Sound(os.path.join("data", "plant.wav"))
sfx_bait_beer = pygame.mixer.Sound(os.path.join("data", "bait_beer.wav"))
sfx_bait_bullion = pygame.mixer.Sound(os.path.join("data", "bait_bullion.mp3"))
sfx_bait_mushroom = pygame.mixer.Sound(os.path.join("data", "bait_mushroom.wav"))
sfx_harvest = pygame.mixer.Sound(os.path.join("data", "harvest.wav"))
sfx_gameover = pygame.mixer.Sound(os.path.join("data", "game_over.wav"))
zombie_sounds = {
    "soda": pygame.mixer.Sound(os.path.join("data", "zombie_soda.wav")),
    "sausage": pygame.mixer.Sound(os.path.join("data", "zombie_sausage.wav")),
    "bun": pygame.mixer.Sound(os.path.join("data", "zombie_bun.wav"))
}

money = 310
available_plants = {'white': 1, 'blue': 1, 'red': 1}
available_baits = {'soda': 1, 'sausage': 1, 'bun': 1}
shop_plants = {'white': 50, 'blue': 75, 'red': 100}
shop_baits = {'soda': 30, 'sausage': 60, 'bun': 80}
seed_colors = {'white': 'gray', 'blue': 'darkblue', 'red': 'darkred'}

seed_images = {
    'white': resize_image(load_image("seed_white.png", -1)),
    'blue': resize_image(load_image("seed_blue.png", -1)),
    'red': resize_image(load_image("seed_red.png", -1))
}
veg_images = {
    'white': resize_image(load_image("veg_white.png", -1)),
    'blue': resize_image(load_image("veg_blue.png", -1)),
    'red': resize_image(load_image("veg_red.png", -1))
}

bait_images = {
    'soda': resize_image(load_image("bait_soda.png")),
    'sausage': resize_image(load_image("bait_sausage.png")),
    'bun': resize_image(load_image("bait_bun.png"))
}

zombie_images = {
    'soda': resize_image(load_image("zombie_soda.png", -1)),
    'sausage': resize_image(load_image("zombie_sausage.png", -1)),
    'bun': resize_image(load_image("zombie_bun.png", -1))
}

weed_images = {
    'flying': resize_image(load_image("kr.jpg", -1)),
    'spiky': resize_image(load_image("wd.jpg", -1)),
    'bouncy': resize_image(load_image("gp.jpg", -1))
}

empty_cell_img = resize_image(load_image("cell_empty.png"))
background_day_img = resize_image(load_image("background_day.png"), (WIDTH * 2, HEIGHT))
background_night_img = resize_image(load_image("background_night.png"), (WIDTH * 2, HEIGHT))
truck_img = resize_image(load_image("truck.png", -1))
shop_bg_img = resize_image(load_image("bg_wd.jpg"), (WIDTH, HEIGHT))
menu_logo = resize_image(load_image("menu_logo.png"))
start_button_img = resize_image(load_image("start_button.png"))

all_sprites = pygame.sprite.Group()
font = pygame.font.Font(None, 36)

picked_plant = ''
picked_i = tuple()
day = 1
night_count = 1


def save_game():
    data = {
        "day": day,
        "money": money,
        "available_plants": available_plants,
        "available_baits": available_baits,
        "night_count": night_count
    }
    with open("save.json", "w") as f:
        json.dump(data, f)


def load_game():
    global day, money, available_plants, available_baits, night_count
    try:
        with open("save.json", "r") as f:
            data = json.load(f)
        day = data["day"]
        money = data["money"]
        available_plants = data["available_plants"]
        available_baits = data["available_baits"]
        night_count = data.get("night_count", 1)
    except:
        pass


save_game()

game_state = "menu"

moving = 0
moving_k = 0
planting_target = 170
defense_target = -630
shop_target = 1200

level_duration = 3600
level_progress = 0
weed_spawn_timer = random.randint(180, 420)
zombies = []
weeds = []


class Ruler:
    def __init__(self, view):
        self.view = view
        self.cell_size = 70
        if view == 1:
            self.size = 3
            self.board = ['white', 'blue', 'red']
            self.left = 170
            self.top = 5
        else:
            self.board = ['soda', 'sausage', 'bun']
            self.size = len(self.board)
            self.left = 170
            self.top = 5

    def render(self, screen):
        for i in range(self.size):
            rect = pygame.Rect(self.left + i * self.cell_size, self.top, self.cell_size, self.cell_size)
            if self.view == 1:
                count = available_plants.get(self.board[i], 0)
                img = seed_images[self.board[i]]
            else:
                count = available_baits.get(self.board[i], 0)
                img = bait_images[self.board[i]]
            screen.blit(img, rect)
            count_text = font.render(str(count), True, pygame.Color('yellow'))
            screen.blit(count_text, (self.left + i * self.cell_size + 10, self.top + self.cell_size + 5))

    def get_cell(self, mouse_pos):
        x, y = mouse_pos
        col = ceil((x - self.left) / self.cell_size)
        if col < 1 or col > self.size or y < self.top or y > self.top + self.cell_size:
            return None, None
        return col, 0

    def on_click(self, mouse_pos):
        global picked_plant, picked_i
        cell = self.get_cell(mouse_pos)
        if cell[0] is None:
            return
        index = cell[0] - 1
        picked_plant = self.board[index]
        if self.view == 1:
            picked_i = (1, index)
        else:
            picked_i = (2, index)

    def unpick(self):
        global picked_plant, picked_i
        picked_plant = ''
        picked_i = tuple()


class Cell:
    def __init__(self):
        self.disabled = 0
        self.num = 0
        self.is_seed = False
        self.plant_color = None
        self.grown = False

    def set(self):
        global picked_plant
        if self.disabled == 0 and picked_plant:
            if available_plants.get(picked_plant, 0) > 0:
                self.plant_color = picked_plant
                self.is_seed = True
                self.grown = False
                available_plants[picked_plant] -= 1
                pygame.mixer.Sound.play(sfx_plant)
        self.disabled = 100

    def harvest(self):
        global money
        if not self.is_seed and self.plant_color:
            money += shop_plants[self.plant_color]
            pygame.mixer.Sound.play(sfx_harvest)
            self.is_seed = True
            self.grown = False

    def grow(self):
        if self.is_seed and self.plant_color:
            self.grown = True
            self.is_seed = False

    def enemy(self, type):
        self.grown = False

    def un_enemy(self):
        self.grown = False

    def draw(self, pos):
        if not self.plant_color:
            screen.blit(empty_cell_img, pos)
        else:
            if self.is_seed:
                screen.blit(seed_images[self.plant_color], pos)
            elif self.grown:
                screen.blit(veg_images[self.plant_color], pos)
            else:
                screen.blit(seed_images[self.plant_color], pos)


class Field:
    def __init__(self):
        self.board = [[Cell() for _ in range(18)] for _ in range(5)]
        self.height = 5
        self.width = 18
        self.cell_size = 70
        self.left = planting_target
        self.top = 175

    def move_towards(self, target, speed):
        if self.left < target:
            self.left += speed
            if self.left > target:
                self.left = target
        elif self.left > target:
            self.left -= speed
            if self.left < target:
                self.left = target

    def render(self, screen):
        if game_state == "defense":
            screen.blit(background_night_img, (0 - (planting_target - self.left), 0))
        else:
            screen.blit(background_day_img, (0 - (planting_target - self.left), 0))
        cs = self.cell_size
        for row in range(self.height):
            for col in range(self.width):
                pos = (self.left + col * cs, self.top + row * cs, cs, cs)
                self.board[row][col].draw(pos)
        for row in range(self.height):
            for col in range(self.width):
                rect = pygame.Rect(self.left + col * cs, self.top + row * cs, cs, cs)
                pygame.draw.rect(screen, pygame.Color('white'), rect, 1)

    def get_cell(self, mouse_pos):
        x, y = mouse_pos
        col = ceil((x - self.left) / self.cell_size)
        row = ceil((y - self.top) / self.cell_size)
        if col < 1 or col > self.width or row < 1 or row > self.height:
            return None, None
        return col, row

    def on_click(self, mouse_pos):
        cell_coords = self.get_cell(mouse_pos)
        if cell_coords[0] is None:
            return
        col, row = cell_coords[0] - 1, cell_coords[1] - 1
        if self.board[row][col].grown:
            self.board[row][col].harvest()
        else:
            self.board[row][col].set()


class Zombie:
    def __init__(self, x, y, bait_type):
        self.x = x
        self.y = y
        self.bait_type = bait_type
        self.size = field.cell_size
        if bait_type == 'sausage':
            self.hp = 3
            self.type = "sausage"
            self.move_delay = 60
            self.emerge_time = 30
        elif bait_type == 'bun':
            self.hp = 1
            self.type = "bun"
            self.move_delay = 30
            self.emerge_time = 20
        else:
            self.hp = 1
            self.type = "soda"
            self.move_delay = 60
            self.emerge_time = 30
        self.move_timer = 0
        self.image = zombie_images.get(self.type, zombie_images["soda"])
        zombie_sounds.get(self.type, zombie_sounds["soda"]).play()

    def move(self):
        if self.emerge_time > 0:
            self.emerge_time -= 1
            return
        if self.move_timer > 0:
            self.move_timer -= 1
            return
        threshold = 3
        target = None
        min_dist = float('inf')
        for w in weeds:
            dist = abs(self.x - w.x) + abs(self.y - w.y)
            if dist < min_dist and dist <= threshold:
                min_dist = dist
                target = w
        if target:
            dx = target.x - self.x
            dy = target.y - self.y
            if abs(dx) >= abs(dy):
                if dx > 0:
                    self.x += 1
                elif dx < 0:
                    self.x -= 1
            else:
                if dy > 0:
                    self.y += 1
                elif dy < 0:
                    self.y -= 1

        self.move_timer = self.move_delay

    def draw(self, screen):
        screen.blit(self.image, (field.left + self.x * field.cell_size, field.top + self.y * field.cell_size))


class Weed:
    def __init__(self, lane, weed_type=None):
        self.x = field.width - 1
        self.y = lane
        self.size = field.cell_size
        self.move_delay = 60
        self.move_timer = 0
        self.type = weed_type if weed_type else random.choice(["flying", "spiky", "bouncy"])
        self.image = weed_images.get(self.type, weed_images["flying"])

    def move(self):
        if self.move_timer > 0:
            self.move_timer -= 1
            return
        if self.type == "flying":
            self.x -= 1
            if random.choice([True, False]):
                self.y += random.choice([-1, 1])
                self.y = max(0, min(field.height - 1, self.y))
        elif self.type == "spiky":
            self.x -= 1
            if random.random() < 0.3:
                self.move_delay = 90
            else:
                self.move_delay = 60
        elif self.type == "bouncy":
            self.x -= 1
            if random.random() < 0.5:
                self.y += random.choice([-1, 1])
                self.y = max(0, min(field.height - 1, self.y))
        self.move_timer = self.move_delay
        if self.x < field.width - 9:
            global game_state
            game_state = "game_over"

    def draw(self, screen):
        screen.blit(self.image, (field.left + self.x * field.cell_size, field.top + self.y * field.cell_size))


def plant_vegetable(mouse_pos):
    field.on_click(mouse_pos)


def plant_bait(mouse_pos):
    cell_coords = field.get_cell(mouse_pos)
    if cell_coords[0] is not None:
        col, row = cell_coords[0] - 1, cell_coords[1] - 1
        if field.board[row][col].plant_color is None:
            if available_baits.get(picked_plant, 0) > 0:
                zombies.append(Zombie(col, row, picked_plant))
                available_baits[picked_plant] -= 1
                print(picked_plant)
                if picked_plant == 'soda':
                    pygame.mixer.Sound.play(sfx_bait_beer)
                elif picked_plant == 'sausage':
                    pygame.mixer.Sound.play(sfx_bait_mushroom)
                elif picked_plant == 'bun':
                    pygame.mixer.Sound.play(sfx_bait_bullion)
                ruler_r.unpick()


def draw_truck():
    if game_state == "planting":
        truck_rect = pygame.Rect(10, 250, 100, 100)
    elif game_state == "shop":
        truck_rect = pygame.Rect(WIDTH - 110, 250, 100, 100)
    else:
        return None
    screen.blit(truck_img, truck_rect)
    return truck_rect


def draw_shop():
    screen.blit(shop_bg_img, (0, 0))
    title = font.render("МАГАЗИН", True, pygame.Color('white'))
    screen.blit(title, (WIDTH // 2 - 40, 20))
    start_x = 100
    start_y = 100
    gap = 20
    cell_size = 70
    i = 0
    for plant, price in shop_plants.items():
        rect = pygame.Rect(start_x + i * (cell_size + gap), start_y, cell_size, cell_size)
        screen.blit(veg_images[plant], rect)
        price_text = font.render(f"{price}", True, pygame.Color('yellow'))
        screen.blit(price_text, (rect.x, rect.y + cell_size + 5))
        i += 1
    i = 0
    for bait, price in shop_baits.items():
        rect = pygame.Rect(start_x + i * (cell_size + gap), start_y + cell_size + 80, cell_size, cell_size)
        screen.blit(bait_images[bait], rect)
        price_text = font.render(f"{price}", True, pygame.Color('yellow'))
        screen.blit(price_text, (rect.x, rect.y + cell_size + 5))
        i += 1
    money_rect = pygame.Rect(10, 10, 150, 50)
    pygame.draw.rect(screen, pygame.Color('grey'), money_rect)
    money_text = font.render(f'Деньги: {money}', True, pygame.Color('yellow'))
    screen.blit(money_text, (15, 15))
    return


def grow_seeds():
    for row in field.board:
        for cell in row:
            if cell.is_seed:
                cell.grow()


def draw_start_screen():
    screen.blit(menu_logo, (WIDTH // 2 - 200, HEIGHT // 2 - 250))
    info_lines = [
        "Добро пожаловать в Zombie Farm!",
        "Днем вы сажаете семена овощей, а ночью ",
        "защищаете ферму",
        "от нашествия сорняков с помощью прикормки.",
        "Используйте магазин для покупки ",
        "дополнительных ресурсов.",
        "Нажмите любую клавишу, чтобы начать."
    ]
    y_offset = HEIGHT // 2 - 100
    for line in info_lines:
        text = font.render(line, True, pygame.Color('white'))
        screen.blit(text, (WIDTH // 2 - 300, y_offset))
        y_offset += 30
    screen.blit(start_button_img, (WIDTH // 2 - 100, HEIGHT - 150))
    pygame.display.flip()


def draw_game_over():
    screen.fill(pygame.Color('black'))
    over_text = font.render("ИГРА ОКОНЧЕНА", True, pygame.Color('red'))
    screen.blit(over_text, (WIDTH // 2 - 120, HEIGHT // 2 - 50))
    restart_text = font.render("Нажмите R для перезагрузки", True, pygame.Color('white'))
    screen.blit(restart_text, (WIDTH // 2 - 180, HEIGHT // 2 + 10))
    pygame.display.flip()


ready_button_rect = pygame.Rect(WIDTH - 150, HEIGHT - 70, 130, 50)
clock = pygame.time.Clock()
fps = 60
run = True

field = Field()
ruler_l = Ruler(1)
ruler_r = Ruler(2)
game_state_transition = ''

game_state = "menu"

while run:
    if game_state == "menu":
        draw_start_screen()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                game_state = "planting"
                save_game()
        clock.tick(fps)
        continue

    screen.fill(pygame.Color('black'))

    if game_state == "shop":
        draw_shop()
    else:
        field.render(screen)

    if game_state != "shop":
        money_rect = pygame.Rect(10, 10, 150, 50)
        pygame.draw.rect(screen, pygame.Color('grey'), money_rect)
        money_text = font.render(f'Деньги: {money}', True, pygame.Color('yellow'))
        screen.blit(money_text, (15, 15))

    if game_state == "planting":
        pygame.draw.rect(screen, pygame.Color('green'), ready_button_rect)
        ready_text = font.render("Я готов", True, pygame.Color('black'))
        text_rect = ready_text.get_rect(center=ready_button_rect.center)
        screen.blit(ready_text, text_rect)
    elif game_state == "defense":
        bar_width = 130
        bar_height = 20
        current_duration = 7200 if night_count == 3 else 3600
        progress = level_progress / current_duration
        progress_width = int(bar_width * progress)
        bar_rect = pygame.Rect(WIDTH - 150, HEIGHT - 70, bar_width, bar_height)
        pygame.draw.rect(screen, pygame.Color('white'), bar_rect, 2)
        inner_rect = pygame.Rect(WIDTH - 150, HEIGHT - 70, progress_width, bar_height)
        pygame.draw.rect(screen, pygame.Color('green'), inner_rect)

    if moving:
        field.left += moving_k * 10
        moving -= 10
        if moving <= 0:
            if game_state_transition == "to_defense":
                field.left = defense_target
                game_state = "defense"
            elif game_state_transition == "to_shop":
                field.left = shop_target
                game_state = "shop"
            elif game_state_transition == "to_planting":
                field.left = planting_target
                game_state = "planting"
                grow_seeds()
                level_progress = 0
                day += 1
                night_count += 1
                save_game()

    if game_state == "defense":
        current_duration = 7200 if night_count == 3 else 3600
        level_progress += 1
        if level_progress >= current_duration:
            if len(weeds) == 0:
                moving = 800
                moving_k = 1
                game_state_transition = "to_planting"
                game_state = ""
                pygame.mixer.music.load(os.path.join("data", "background_music.mp3"))
                pygame.mixer.music.play(-1)
        if weed_spawn_timer > 0:
            weed_spawn_timer -= 1
        else:
            lane = random.randint(0, field.height - 1)
            weed_type = random.choice(["flying", "spiky", "bouncy"])
            weeds.append(Weed(lane, weed_type))
            weed_spawn_timer = random.randint(180, 420)

    for weed in weeds[:]:
        weed.move()
        weed.draw(screen)
        for zombie in zombies[:]:
            if weed.x == zombie.x and weed.y == zombie.y:
                if zombie.type == "sausage":
                    zombie.hp -= 1
                    if zombie.hp <= 0:
                        zombies.remove(zombie)
                else:
                    zombies.remove(zombie)
                if weed in weeds:
                    weeds.remove(weed)

    for zombie in zombies:
        zombie.move()
        zombie.draw(screen)

    if game_state == "planting":
        ruler_l.render(screen)
    elif game_state == "defense":
        ruler_r.render(screen)

    all_sprites.draw(screen)

    truck_rect = draw_truck()

    pygame.display.flip()

    if game_state == "game_over":
        draw_game_over()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.unicode.lower() == 'r':
                    load_game()
                    field = Field()
                    zombies = []
                    weeds = []
                    level_progress = 0
                    game_state = "planting"
        clock.tick(fps)
        continue

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
            if game_state == "planting":
                if event.unicode == 'z':
                    picked_plant = 'white'
                if event.unicode == 'x':
                    picked_plant = 'blue'
                if event.unicode == 'c':
                    picked_plant = 'red'
            elif game_state == "defense":
                if event.unicode == 'z':
                    picked_plant = 'soda'
                if event.unicode == 'x':
                    picked_plant = 'sausage'
                if event.unicode == 'v':
                    picked_plant = 'bun'
                if event.unicode == 'p':
                    level_progress += 100
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if game_state == "planting":
                    if truck_rect and truck_rect.collidepoint(event.pos):
                        game_state = "shop"
                    elif ready_button_rect.collidepoint(event.pos):
                        pygame.mixer.music.load(os.path.join("data", "background_night_music.mp3"))
                        pygame.mixer.music.play(-1)
                        moving = 800
                        moving_k = -1
                        game_state_transition = "to_defense"
                        level_progress = 0
                        weed_spawn_timer = random.randint(180, 420)
                    else:
                        plant_vegetable(event.pos)
                        ruler_l.on_click(event.pos)
                elif game_state == "defense":
                    plant_bait(event.pos)
                    ruler_r.on_click(event.pos)
                elif game_state == "shop":
                    x, y = event.pos
                    shop_item_width = 70
                    shop_item_gap = 20
                    start_x = 100
                    start_y = 100
                    for i, (plant, price) in enumerate(shop_plants.items()):
                        rect = pygame.Rect(start_x + i * (shop_item_width + shop_item_gap), start_y, shop_item_width,
                                           shop_item_width)
                        if rect.collidepoint(event.pos):
                            if money >= price:
                                money -= price
                                available_plants[plant] += 1
                    for i, (bait, price) in enumerate(shop_baits.items()):
                        rect = pygame.Rect(start_x + i * (shop_item_width + shop_item_gap),
                                           start_y + shop_item_width + 80, shop_item_width, shop_item_width)
                        if rect.collidepoint(event.pos):
                            if money >= price:
                                money -= price
                                available_baits[bait] += 1
                    if truck_rect and truck_rect.collidepoint(event.pos):
                        game_state = "planting"
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                if game_state == "defense":
                    lane = random.randint(0, field.height - 1)
                    weeds.append(Weed(lane))
    clock.tick(fps)

pygame.quit()
