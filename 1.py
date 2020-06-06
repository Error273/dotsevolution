import pygame
import random
from math import sqrt
import datetime as dt
import xlsxwriter

WIDTH = 600
HEIGHT = 600
FPS = 100

# Задаем цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

GEN_AMOUNT = 300  # кол во экземпляров в одном поколении

# сбор инфы

workbook = xlsxwriter.Workbook('dataa.xlsx')
worksheet = workbook.add_worksheet()
data = []


def check_all_dead(gen):
    """Проверяет, все ли в покалении мертвы"""
    for i in gen:
        if not i.dead:
            return False
    return True


def intersection(obj1, obj2):
    """Проверяет коллизию двух объектов"""
    if obj2.__class__.__name__ == 'Finish':
        x1 = obj1.x
        y1 = obj1.y
        x2 = obj1.x + obj1.radius
        y2 = obj1.y + obj1.radius
        x3 = obj2.x
        y3 = obj2.y
        x4 = obj2.x + obj2.radius
        y4 = obj2.y + obj2.radius
        x5 = max(x1, x3)
        y5 = max(y1, y3)
        x6 = min(x2, x4)
        y6 = min(y2, y4)
        # no intersection
        if x5 >= x6 or y5 >= y6:
            return False
        return True
    else:
        x1 = obj1.x
        y1 = obj1.y
        x2 = obj1.x + obj1.radius
        y2 = obj1.y + obj1.radius
        x3, y3, x4, y4 = obj2.get_coords()
        x5 = max(x1, x3)
        y5 = max(y1, y3)
        x6 = min(x2, x4)
        y6 = min(y2, y4)
        # no intersection
        if x5 >= x6 or y5 >= y6:
            return False
        return True


class Dot:
    """Точка, экземпляр, обучаемый объект"""

    def __init__(self, color, x, y, radius, screen, point, *blocks):
        self.color = color
        self.x = x
        self.y = y
        self.screen = screen
        self.radius = radius
        self.point = point  # объект, которого нужно достигнуть
        self.blocks = blocks  # список препятсвий
        # мозг. является списком состоящем из двумерных векторов.
        # каждое значение вектора определяет, на сколько стоит сдвинуть x или y
        self.brain = [(random.choice([-10, 10, 0]), random.choice([-10, 10, 0])) for i in range(500)]
        # шаг в мозгу, на котором сейчас находится экземпляр
        self.step = 0
        # проверка, жив ли экземляр
        self.dead = False
        # проверка, достиг ли точки экземляр
        self.victory = False
        # время, когда создался экземпляр
        self.start_time = dt.datetime.now()
        # время, когда экземпляр выиграл
        self.end_time = False

    def check_condition(self):
        """Не вышел ли объект за экран. если да, убить"""
        if self.x <= 0 or self.x >= 600 or self.y <= 0 or self.y >= 600:
            self.dead = True
        """Проверка, долстиг ли экземляр цели"""
        if intersection(self, self.point):
            self.victory = True
        """Проверка, не ударился ли экземпял об стену"""
        for block in self.blocks:
            if intersection(self, block):
                self.dead = True
        """Сохраняем время, когда экземпляр выиграл"""
        if self.victory and not self.end_time:
            self.end_time = dt.datetime.now()

    def update(self):
        """Движение"""
        self.check_condition()
        pygame.draw.circle(self.screen, self.color, (self.x, self.y), self.radius)
        x_move, y_move = self.brain[self.step]
        if not self.dead and not self.victory:
            self.x += x_move
            self.y += y_move
        self.step += 1

    def set_color(self, color):
        """Устновить цвет"""
        self.color = color

    def reset_steps(self):
        """обнулить шаги"""
        self.step = 0

    def get_brains(self):
        """Получить мозг"""
        return self.brain

    def set_brains(self, brain):
        """Установить мозг"""
        self.brain = brain

    def get_creation_time(self):
        return self.start_time

    def get_end_time(self):
        return self.end_time


class Finish:
    """Точка, цель"""

    def __init__(self, color, x, y, radius, screen):
        self.color = color
        self.x = x
        self.y = y
        self.radius = radius
        self.screen = screen

    def update(self):
        pygame.draw.circle(self.screen, self.color, (self.x, self.y), self.radius)


class Block:
    """Препятствие"""

    def __init__(self, color, x, y, width, height, screen):
        self.color = color
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.screen = screen

    def get_coords(self):
        return self.x, self.y, self.x + self.width, self.y + self.height

    def update(self):
        pygame.draw.rect(self.screen, self.color, (self.x, self.y, self.width, self.height))


# Создаем игру и окно, шрифты
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("MACHINE")
clock = pygame.time.Clock()
finish = Finish(GREEN, 300, 100, 15, screen)
block = Block(BLUE, 0, 200, 400, 50, screen)
font = pygame.font.Font(None, 36)

generations = 1  # кол-во поколений с начала игры


def fitness_function(obj, point):
    """Насколько хорошо делает экземляр"""
    if not obj.dead:
        d = sqrt((point.x - obj.x) ** 2 + (point.y - obj.y) ** 2)
        if obj.victory:
            time_took = (obj.get_end_time() - obj.get_creation_time()).total_seconds()
            d += time_took
        return d
    else:
        return 666


def create_gen(*best):
    global generations
    """создать новое покаление"""
    result = []
    if best:
        for i in range(GEN_AMOUNT - 1):
            new_brain = best[0].get_brains()[:]
            #  мутируем мозг
            for m in range(len(new_brain)):
                if random.randint(1, 25) == 1:
                    new_brain[m] = (random.choice([10, -10, 0]), random.choice([-10, 10, 0]))
            new_guy = Dot(BLACK, 300, 500, 5, screen, finish, block)
            new_guy.set_brains(new_brain)
            result.append(new_guy)
        # чувак с предыдущего покаления
        oldguy = Dot(BLACK, 300, 500, 5, screen, finish, block)
        oldguy.set_brains(best[0].get_brains()[:])
        oldguy.set_color(RED)
        result.append(oldguy)
    else:
        result = [Dot(BLACK, 300, 500, 5, screen, finish, block) for i in range(GEN_AMOUNT)]
    return result


def evolve():
    """эволюция, генетический алгоритм"""
    global generations
    global dots
    global finish
    global data
    for dot in dots:
        if dot.step == 500 or check_all_dead(dots):
            generations += 1
            # мутация ------------
            bestresult = 666
            bestguy = None
            for i in dots:
                if fitness_function(i, finish) <= bestresult:
                    bestresult = fitness_function(i, finish)
                    bestguy = i
            if not bestguy.victory and generations % 10 == 0:
                dots = create_gen()
            else:
                dots = create_gen(bestguy)
                if bestguy.get_end_time():
                    data.append(fitness_function(bestguy, finish))
                    print(data[-1])
            break
        else:
            dot.update()


dots = create_gen()  # создаем начальное покаление
# Цикл игры
running = True
while running:
    # Держим цикл на правильной скорости
    clock.tick(FPS)
    # Ввод процесса (события)
    for event in pygame.event.get():
        # check for closing window
        if event.type == pygame.QUIT:
            running = False

    screen.fill(WHITE)

    finish.update()
    block.update()

    evolve()

    text = font.render(f'Gens: {generations}', 0, BLACK)
    screen.blit(text, (0, 0))
    # После отрисовки всего, переворачиваем экран
    pygame.display.flip()

pygame.quit()
for row, thing in enumerate(data):
    worksheet.write(row, 0, thing)
    worksheet.write(row, 1, row)
chart = workbook.add_chart({'type': 'line'})
chart.add_series({'categories': f'=Sheet1!B1:B{len(data)}', 'values': f'=Sheet1!A1:A{len(data)}'})
worksheet.insert_chart('C1', chart)
workbook.close()
