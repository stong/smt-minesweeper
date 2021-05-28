# SMT Minesweeper Solver

Written for a class project for Intro to Algorithms (CS 3510) at Georgia Tech in Spring 2021.

It models the problem as 0-1 Integer Programming, and uses Z3 to simplify and bit-blast to boolean SAT. There are two solver backends: one using Z3 directly and one using my own recursive backtracker.

## Interesting files

 - `minesweeperAI2.py` - Solver using my backtracker
 - `minesweeperAI2_z3.py` - Solver using Z3 SAT backend

The code is, of course, not the best because I wrote it all in the last few hours before deadline (since I procrastinated for 3 weeks Lol)
