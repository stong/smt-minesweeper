import numpy as np
import random
from collections import deque
from z3 import *

class CellState:
    def __init__(self):
        self.value = -1  # -1 = unknown, 9 = bomb, rest = number
        self.known_clear = False
        self.neighbor_bombs = 0  # how many neighbor bombs are accounted for
        self.neighbor_clear = 0  # how many neighbor non-bombs are accounted for
        self.updatecount = 0

class AI2:

    # Define settings upon initialization. Here you can specify
    def __init__(self, numRows, numCols, numBombs, safeSquare):

        # game variables that can be accessed in any method in the class. For example, to access the number of rows, use "self.numRows"
        self.num_rows = numRows
        self.num_cols = numCols
        self.num_bombs = numBombs
        self.num_cells = self.num_rows * self.num_cols

        self.known_bombs = set()
        self.board_state = None

        self.queue = deque()
        self.opened = set()
        self.opened.add(safeSquare)

        self.prev_move = safeSquare

        self.dirty_tiles = set()

        self.total_sat_solve_steps = 0
        self.total_sat_solves = 0
        self.total_sat_variables = 0

        self.vars = {}
        for r in range(self.num_rows):
            for c in range(self.num_cols):
                var = Int('x_%d_%d' % (r,c))
                self.vars[(r,c)] = var

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

    def choose_square(self):
        if self.queue:
            to_open = self.queue.popleft()
            row, col = to_open
            return row, col

        # umm... we have no idea just choose random one I guess
        print("We have to guess")

        if self.dirty_tiles:
            return random.choice(list(self.dirty_tiles))

        unopened_squares = []
        for row in range(self.num_rows):
            for col in range(self.num_cols):
                if (row,col) not in self.opened and (row,col) not in self.known_bombs:
                    unopened_squares.append((row, col))
        return random.choice(unopened_squares)

    # Use recursive backtracking to solve SAT.
    def backtrack(self, circuit, variables, assigns):
        steps = 1
        circuit = simplify(circuit)
        if circuit.eq(BoolVal(True)):
            return 'sat', steps # found satisfying solution! :)
        elif circuit.eq(BoolVal(False)): # this backtracking branch is dead
            return 'unsat', steps
        if len(assigns) == len(variables):
            assert False # reached end of backtracking tree (all free variables assigned), yet neither True nor False?

        try_var = variables[len(assigns)]

        # try true
        assigns_t = assigns + [(try_var, BoolVal(True))]
        result_t, steps_t = self.backtrack(substitute(circuit, *assigns_t), variables, assigns_t)
        steps += steps_t
        if result_t == 'sat':
            return 'sat', steps

        # try false
        assigns_f = assigns + [(try_var, BoolVal(False))]
        result_f, steps_f = self.backtrack(substitute(circuit, *assigns_f), variables, assigns_f)
        steps += steps_f
        if result_f == 'sat':
            return 'sat', steps

        if result_t == 'unsat' and result_f == 'unsat': # both possibilities unsat? whole thing is unsat
            return 'unsat', steps

        assert False # ???

    # Solve a boolean circuit satisfiability problem using a recursive backtracker.
    def sat_solve(self, clauses):
        clauses = [simplify(clause) for clause in clauses]
        variables = {}
        def get_vars(expr):
            if is_const(expr):
                if expr.decl().kind() == Z3_OP_UNINTERPRETED and str(expr) not in variables:
                    variables[str(expr)] = expr
            else:
                for c in expr.children():
                    get_vars(c)
        for clause in clauses:
            get_vars(clause)

        is_sat, steps = self.backtrack(And(*clauses), list(variables.values()), [])
        self.total_sat_solve_steps += steps
        self.total_sat_variables += len(variables)
        self.total_sat_solves += 1
        print('SAT solve with %d variables took %d steps' % (len(variables), steps))
        return is_sat

    def linear_programming_to_sat(self, lp_problem):
        tactic = Then(With('simplify', arith_lhs=True, som=True),
                 'normalize-bounds',  # bounded arithmetic -- we are doing 0-1 integer programming
                 'lia2pb',  # linear integer arithmetic to pseudo-boolean
                 'pb2bv',  # pseudo-boolean to bit-vectors
                 'simplify','propagate-values','solve-eqs','symmetry-reduce','macro-finder','special-relations', 'reduce-bv-size', 'max-bv-sharing','propagate-bv-bounds-new','bv_bound_chk', # throw a bunch of simplification steps on it
                 'bv1-blast', # bit-vectors to SAT
                 'simplify', 'propagate-values', 'solve-eqs','symmetry-reduce','macro-finder','special-relations', 'aig' # throw some more simplification on it
        )
        boolean_circuit = tactic(lp_problem)
        assert len(boolean_circuit) == 1
        clauses = boolean_circuit[0]
        return clauses

    def recompute(self, board_state):
        cur_dirty = set(self.dirty_tiles)
        self.dirty_tiles.clear()

        s = Goal()
        candidates = set()
        for r in range(self.num_rows):
            for c in range(self.num_cols):
                if 0 <= board_state[r][c] <= 8:
                    any_unknown_neighbor = any([board_state[n_r][n_c] == -1 and (n_r, n_c) not in self.known_bombs and (n_r,n_c) in cur_dirty for n_r, n_c in self.neighbors(r, c)])
                    if any_unknown_neighbor:
                        expr = 0
                        for n_r, n_c in self.neighbors(r, c):
                            expr += self.vars[(n_r, n_c)]
                            if (n_r, n_c) in self.known_bombs or board_state[n_r][n_c] == 9:
                                s.add(self.vars[(n_r,n_c)] == 1)
                            elif 0 <= board_state[n_r][n_c] <= 8:
                                s.add(self.vars[(n_r,n_c)] == 0)
                            else:
                                # this cell is still unknown
                                candidates.add((n_r,n_c))
                                s.add(Or(self.vars[(n_r, n_c)] == 0, self.vars[(n_r, n_c)] == 1))
                        s.add(expr == int(board_state[r][c]))

        assert self.sat_solve(self.linear_programming_to_sat(s)) == 'sat'

        for r, c in candidates:
            if (r, c) in self.opened or (r, c) in self.known_bombs: # don't needlessly repeat work
                continue

            if (r, c) not in cur_dirty: # we have no new info about this
                continue

            # is it possible for bomb to be here?
            s_ = s.__copy__()
            s_.add(self.vars[r, c] == 1)
            if self.sat_solve(self.linear_programming_to_sat(s_)) == 'unsat': # no, bomb is definitely NOT possible here! so this tile is safe
                print (f'{r},{c} is safe')
                s.add(self.vars[r, c] == 0)
                self.opened.add((r,c))
                self.queue.append((r,c))
            else:
                # is it possible for bomb to NOT be here?
                s_ = s.__copy__()
                s_.add(self.vars[r, c] == 0)
                if self.sat_solve(self.linear_programming_to_sat(s_)) == 'unsat': # no, bomb is DEFINITELY here! so this is bomb tile
                    print (f'{r},{c} is bomb')
                    self.known_bombs.add((r, c))
                    self.make_neighbors_dirty(r, c)
                    s.add(self.vars[r, c] == 1)


    def make_neighbors_dirty(self, opened_row, opened_col):
        if (opened_row, opened_col) in self.dirty_tiles:
            self.dirty_tiles.remove((opened_row, opened_col))
        for n_r, n_c in self.neighbors(opened_row, opened_col):
            if self.board_state[n_r][n_c] == -1 and (n_r, n_c) not in self.opened and (n_r, n_c) not in self.known_bombs:
                self.dirty_tiles.add((n_r, n_c))

    def performAI(self, board_state):
        opened_row, opened_col = self.prev_move
        self.board_state = board_state
        if board_state[opened_row][opened_col] == 9:
            print('We opened a bomb! :(')
            self.known_bombs.add((opened_row, opened_col))
        elif board_state[opened_row][opened_col] == 0: # Optimization: open all neighbors of 0
            for r, c in self.neighbors(opened_row, opened_col):
                if (r,c) not in self.opened:
                    self.opened.add((r,c))
                    self.queue.append((r, c))
        self.make_neighbors_dirty(opened_row, opened_col)

        if not self.queue:
            self.recompute(board_state)

        if len(self.known_bombs) == self.num_bombs:
            print(f"List of bombs is {self.known_bombs}")
            return self.submit_final_answer_format(list(self.known_bombs))

        to_open = self.choose_square()
        self.prev_move = to_open
        self.opened.add(to_open)
        print(f"Square to open is {to_open}")

        return self.open_square_format(to_open)
