import numpy as np
import random
from collections import deque

class CellState:
    def __init__(self):
        self.value = -1  # -1 = unknown, 9 = bomb, rest = number
        self.known_clear = False
        self.neighbor_bombs = 0  # how many neighbor bombs are accounted for
        self.neighbor_clear = 0  # how many neighbor non-bombs are accounted for
        self.updatecount = 0

class AI1:

    # Define settings upon initialization. Here you can specify
    def __init__(self, numRows, numCols, numBombs, safeSquare):   

        # game variables that can be accessed in any method in the class. For example, to access the number of rows, use "self.numRows" 
        self.num_rows = numRows
        self.num_cols = numCols
        self.num_bombs = numBombs

        self.queue = deque()
        self.cells = [[CellState() for c in range(self.num_cols)] for r in range(self.num_rows)]
        self.known_bombs = []

        self.prev_move = safeSquare

    def open_square_format(self, squareToOpen):
        return ("open_square", squareToOpen)

    def submit_final_answer_format(self, listOfBombs):
        return ("final_answer", listOfBombs)

    def neighbors(self, row, col):
        for r in range(row - 1, row + 2):
            if r < 0 or r >= self.num_rows:
                continue
            for c in range(col - 1, col + 2):
                if c < 0 or c >= self.num_cols:
                    continue
                if r == row and c == col:
                    continue
                yield r, c

    def on_cell_update(self, row, col):
        cell = self.cells[row][col]
        if cell.value >= 0 and cell.value != 9:
            assert cell.neighbor_bombs <= cell.value
            assert cell.neighbor_clear <= 8 - cell.value
            if cell.neighbor_bombs == cell.value:
                # all neighboring bombs accounted for, rest must be clear
                for r, c in self.neighbors(row, col):
                    self.queue.append((r, c))
                    # self.update(r, c)
            if cell.neighbor_clear == len(list(self.neighbors(row, col))) - cell.value:
                # all neighbors accounted for, rest must be bombs
                for r, c in self.neighbors(row, col):
                    if self.cells[r][c].value == -1:
                        self.cells[r][c].value = 9
                        self.update(r, c)

    def update(self, row, col):
        cell = self.cells[row][col]

        cell.updatecount += 1
        assert cell.updatecount == 1

        assert cell.value != -1

        if cell.value == 9:
            assert (row, col) not in self.known_bombs
            self.known_bombs.append((row, col))

        for r, c in self.neighbors(row, col):
            neighbor = self.cells[r][c]
            if cell.value == 9:
                neighbor.neighbor_bombs += 1
                assert neighbor.neighbor_bombs <= 8
                self.on_cell_update(r, c)
            else:
                neighbor.neighbor_clear += 1
                assert neighbor.neighbor_clear <= 8
                self.on_cell_update(r, c)

        self.on_cell_update(row, col)

        # for r in self.cells:
        #     print('|',end='')
        #     for c in r:
        #         s = f'{c.value}/{c.neighbor_clear}/{c.neighbor_bombs}'
        #         # s = f'{c.value}/{c.neighbor_clear}'
        #         s = s.rjust(6, ' ')
        #         print(s , end='|')
        #     print('')
        # print('')

    def choose_square(self):
        while self.queue:
            to_open = self.queue.popleft()
            row, col = to_open
            if self.cells[row][col].value != -1: # already opened
                continue
            print("From queue")
            return row, col

        # umm... we have no idea just choose random one I guess
        print("We have to guess")
        unopened_squares = []
        for row in range(self.num_rows):
            for col in range(self.num_cols):
                if self.cells[row][col].value == -1 and (row,col) not in self.known_bombs:
                    unopened_squares.append((row, col))
        return random.choice(unopened_squares)

    def performAI(self, board_state):
        # update our known info
        row, col = self.prev_move
        self.cells[row][col].value = board_state[row][col]

        # trigger updates
        self.update(row, col)

        if len(self.known_bombs) == self.num_bombs:
            print(f"List of bombs is {self.known_bombs}")
            return self.submit_final_answer_format(self.known_bombs)

        to_open = self.choose_square()
        print(f"Square to open is {to_open}")
        self.prev_move = to_open

        return self.open_square_format(to_open)
