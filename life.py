import logging
import pygame
from pathos.multiprocessing import ProcessingPool
from random import random


class Grid:
    def __init__(self, columns, rows, populate=('random', 0.25), processes=1,
                 torus=True):
        self.torus = torus
        self.columns = columns
        self.rows = rows
        if populate[0] == 'random':
            self.grid = self.fill_grid_random(fill=populate[1])
        else:
            raise ValueError('populate parameter only supports "random"')
        self.sections = self.split_grid(processes)

    def fill_grid_random(self, fill=0.25):
        logging.debug('filling grid randomly')
        return [[Cell(Cell.alive, {'col': col, 'row': row}, self)
                 if random() < fill else
                 Cell(Cell.dead, {'col': col, 'row': row}, self)
                 for col in range(self.columns)] for row in range(self.rows)]

    def print(self, debug=False):
        for row in self.grid:
            for cell in row:
                if debug:
                    cell._debug_print()
                else:
                    cell.print()
            print()

    def update_section(self, section):
        y_min, y_max, x_min, x_max = section
        for row in self.grid[y_min:y_max]:
            for cell in row[x_min:x_max]:
                nn = cell.count_neighbors()
                if cell.state is Cell.alive:
                    if nn < 2 or nn > 3:
                        cell.next_state = Cell.dead
                    else:
                        cell.next_state = Cell.alive
                else:
                    if nn == 3:
                        cell.next_state = Cell.alive
                    else:
                        cell.next_state = Cell.dead

    def update_mp(self):
        results = ProcessingPool.map(self.update_section, self.sections)

    def split_grid(self, processes):
        '''Return list of (y_min, y_max, x_min, x_max) rectangles'''
        if processes not in [1, 2, 4]:
            raise ValueError("We currently only support 1, 2, or 4 sections")
        sections = []
        y_min = 0
        y_mid = int(self.rows / 2)
        y_max = self.rows
        x_min = 0
        x_mid = int(self.columns / 2)
        x_max = self.columns
        if processes == 1:
            sections.append((y_min, y_max, x_min, x_max))
        elif processes == 2:
            if self.columns >= self.rows:  # vertical split
                sections.append((y_min, y_max, x_min, x_mid))
                sections.append((y_min, y_max, x_mid, x_max))
            else:
                sections.append((y_min, y_mid, x_min, x_max))
                sections.append((y_mid, y_max, x_min, x_max))
        elif processes == 4:
            # top left
            sections.append((y_min, y_mid, x_min, x_mid))
            # bottom left
            sections.append((y_mid, y_max, x_min, x_mid))
            # top right
            sections.append((y_min, y_mid, x_mid, x_max))
            # bottom right
            sections.append((y_mid, y_max, x_mid, x_max))
        return sections

    def repopulate(self):
        for row in self.grid:
            for cell in row:
                if cell.next_state is not None:
                    cell.state = cell.next_state
                cell.next_state = None


class Cell:
    alive = True
    dead = False

    def __init__(self, state, coords, grid):
        self.state = state
        self.coords = coords
        self.grid = grid
        self.next_state = None

    def _debug_print(self):
        print((f"| y:{self.coords['row']} x:{self.coords['col']} "
               f"a:{self.state} n:{self.count_neighbors()}"), end='')

    def count_neighbors(self):
        top_row = (self.coords['row'] - 1) % self.grid.rows
        middle_row = self.coords['row']
        bottom_row = (self.coords['row'] + 1) % self.grid.rows
        left_col = (self.coords['col'] - 1) % self.grid.columns
        middle_col = self.coords['col']
        right_col = (self.coords['col'] + 1) % self.grid.columns
        neighbors = [self.grid.grid[top_row][left_col],
                     self.grid.grid[top_row][middle_col],
                     self.grid.grid[top_row][right_col],
                     self.grid.grid[middle_row][left_col],
                     self.grid.grid[middle_row][right_col],
                     self.grid.grid[bottom_row][left_col],
                     self.grid.grid[bottom_row][middle_col],
                     self.grid.grid[bottom_row][right_col]]
        logging.debug(f'neighborhood: {neighbors}')
        count = 0
        for cell in neighbors:
            if cell.state is Cell.alive:
                count += 1
        return count

    def draw(self):
        pass

    def print(self):
        if self.state is Cell.alive:
            print('O', end='')
        else:
            print(' ', end='')


class Screen:
    def __init__(self, grid, cell_size):
        '''the width and height params are grid cells, not pixels'''
        self.grid = grid
        self.cell_size = cell_size
        self.res_width = grid.columns * cell_size
        self.res_height = grid.rows * cell_size
        self.size = (self.res_width, self.res_height)
        self.screen = pygame.display.set_mode(self.size)

    def draw(self):
        size = (self.cell_size, self.cell_size)
        for y, row in enumerate(self.grid.grid):
            for x, cell in enumerate(row):
                coords = (x*self.cell_size, y*self.cell_size)
                if cell.state is Cell.alive:
                    color = pygame.Color('white')
                else:
                    color = pygame.Color('black')
                self.screen.fill(color, rect=pygame.Rect(coords, size))
        pygame.display.update()
