# SMT Minesweeper Solver

Written for a class project for Intro to Algorithms (CS 3510) at Georgia Tech in Spring 2021.

It models the problem as 0-1 Integer Programming, and uses Z3 to simplify and bit-blast to boolean SAT. There are two solver backends: one using Z3 directly and one using my own recursive backtracker.

https://user-images.githubusercontent.com/14918218/119922564-0c4a3700-bf3e-11eb-98f5-46722c43aed6.mp4

## Interesting files

 - `minesweeperAI2.py` - Solver using my backtracker
 - `minesweeperAI2_z3.py` - Solver using Z3 SAT backend

The code is, of course, not the best because I wrote it all in the last few hours before deadline (since I procrastinated for 3 weeks Lol)
