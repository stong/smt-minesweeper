import numpy as np
import sys
np.set_printoptions(threshold=sys.maxsize)
from tkinter import *
import random
import minesweeperAI1 
import minesweeperAI2
import json
import argparse

# Here, we are creating our class, Window, and inheriting from the Frame
# class. Frame is a class from the tkinter module. (see Lib/tkinter/__init__)
class Window(Frame):

    # Define settings upon initialization. Here you can specify
    def __init__(self, testcase_filename, master=None):
        
        # parameters that you want to send through the Frame class. 
        Frame.__init__(self, master)   

        #reference to the master widget, which is the tk window                 
        self.master = master

        #with that, we want to then run init_window, which doesn't yet exist
        self.outcome = 0

        with open(testcase_filename) as fp:
            data = json.load(fp)

        boardSize = data['dim'].split(',')
        safe = data['safe'].split(',')

        # game variables that can be accessed in any method in the class. For example, to access the number of rows, use "self.numRows"         
        self.numRows = int(boardSize[0])
        self.numCols = int(boardSize[1])
        self.numBombs = int(data['bombs'])
        self.safeSquare = (int(safe[0]), int(safe[1]))
        self.gridInput = data['board']

        print(self.numRows, self.numCols, self.numBombs, self.safeSquare, self.gridInput)

        self.init_window()

    # Creation of init_window
    def init_window(self):
        # changing the title of our master widget      
        self.master.title("Minesweeper")

        # allowing the widget to take the full space of the root window
        self.pack(fill=BOTH, expand=1)
        
        self.button = []
        for row in range(self.numRows):
            curRow = []
            for col in range(self.numCols):
                curRow.append(Button(self, bg="gray", width=2, height=1, command=lambda rw=row, cl=col: self.open_button(rw, cl)))
                curRow[col].grid(row=row, column=col)
            self.button.append(curRow)

        self.create_board()
        AIAlgo1Button = Button(self, bg="blue", text="AI 1", width=6, height=5, command=self.AIAlgo1)
        AIAlgo1Button.place(x=6000, y=1500)
        self.AI1 = minesweeperAI1.AI1(self.numRows, self.numCols, self.numBombs, self.safeSquare)

        AIAlgo2Button = Button(self, bg="blue", text="AI 2", width=6, height=5, command=self.AIAlgo2)
        AIAlgo2Button.place(x=600, y=350)
        self.AI2 = minesweeperAI2.AI2(self.numRows, self.numCols, self.numBombs, self.safeSquare)

        self.highlight_button(self.safeSquare)

    # (DO NOT MODIFY): uncover a square and perform appriopriate action based on game rule
    def open_button(self, r, c):

        if not self.squareInBounds(r, c):
            return

        self.button[r][c].config(state="disabled")
        if self.ans[r][c] != 9:
            self.button[r][c]["text"] = self.ans[r][c]
            self.button[r][c]["bg"] = "white"
        else:
            self.button[r][c]["text"] = self.ans[r][c]
            self.button[r][c]["bg"] = "red"

    # (helper function): return true if and only if all non-bomb squares have been uncovered (game is won) 
    def isGameWon(self):
        cnt = 0
        for row in range(self.numRows):
            for col in range(self.numCols):
                if self.button[row][col]['state'] != 'disabled': cnt += 1
        return cnt == self.numBombs

    # (helper function): return true if and only if a square (r, c) is within the game grid
    def squareInBounds(self, r, c):
        return r >= 0 and c >= 0 and r < self.numRows and c < self.numCols

    # (helper function): return true if and only if the board has all covered (unopened) squares
    def isNewBoard(self):
        for row in range(self.numRows):
            for col in range(self.numCols):
                if self.button[row][col]['state'] == 'disabled':
                    return False
        return True   

    # (helper function): change the color of specified square to blue to indicate this is the square you will select next
    def highlight_button(self, square):
        if self.squareInBounds(square[0], square[1]):
            self.button[square[0]][square[1]]["bg"] = "blue"  

    # (helper function): get the current board state from player POV. Note -1 represents unknown square
    def getBoardState(self):
        board = np.full((self.numRows, self.numCols), -1)
        for row in range(self.numRows):
            for col in range(self.numCols):
                value = 0
                if self.button[row][col]['state'] == 'disabled':
                    if self.button[row][col]["text"] != "":
                        value = int(self.button[row][col]["text"])
                    board[row][col] = value
        return board

    # generate a board based on test case input
    def create_board(self):

        self.ans = np.full((self.numRows, self.numCols), 0)
        self.bombLocations = [(i % self.numCols, int(i/self.numCols)) for i, c in enumerate(self.gridInput) if c == 9 or c == '9']
        # Add numbers 0-8 to the ans grid 
        for row in range(self.numRows):
            for col in range(self.numCols):
                self.ans[col][row] = self.gridInput[row * self.numCols + col]

        print(f"starting board\n{self.ans}")
        print(f"location of bombs: {self.bombLocations}")

    # parse the user's command and perform the appropriate action.
    def parseAIAlgo(self, userCommand):
        if type(userCommand) is not tuple:
            print("cannot parse command")
        elif "open_square" in userCommand[0]:
            self.nextSquareToOpen = userCommand[1]
            self.highlight_button(self.nextSquareToOpen)
        elif "final_answer" in userCommand[0]:
            userAnswer = userCommand[1]
            self.numDigs = np.count_nonzero(self.getBoardState() != -1)
            if set(self.bombLocations) == set(userAnswer):
                self.outcome = 1
                print(f"CORRECT BOMB LIST! You performed {self.numDigs} digs")
            else:
                self.outcome = -1
                print(f"WRONG BOMB LIST. expected: {self.bombLocations}, received: {userAnswer}. You performed {self.numDigs} digs")

    """
    Each time you click the button, We would recommend you to perform the following loop in your algorithm:
    1) uncover the best square computed last iteration using `self.open_button(r, c)`. Note a safe square is given for the first iteration
    2) perform your algorithm to find the best square using performAI1()
    3) visually display the square you will select on the next iteration (blue square) using self.highlight_button(r, c)
    """
    def AIAlgo1(self):
        if self.outcome != 0:
            return # game is already over (won or loss)

        if self.isNewBoard():
            self.open_button(self.safeSquare[0], self.safeSquare[1])
        else:
            self.open_button(self.nextSquareToOpen[0], self.nextSquareToOpen[1])

        if self.outcome != 0:
            return # game is already over (won or loss)
        
        boardState = self.getBoardState()
        userCommand = self.AI1.performAI(boardState)
        self.parseAIAlgo(userCommand)
        for r,c in self.AI1.known_bombs:
            self.button[r][c]["bg"] = "yellow"



    def AIAlgo2(self):
        if self.outcome != 0:
            return # game is already over (won or loss)

        if self.isNewBoard():
            self.open_button(self.safeSquare[0], self.safeSquare[1])
        else:
            self.open_button(self.nextSquareToOpen[0], self.nextSquareToOpen[1])
        
        if self.outcome != 0:
            return # game is already over (won or loss)

        boardState = self.getBoardState()
        userCommand = self.AI2.performAI(boardState)
        self.parseAIAlgo(userCommand)
        for r,c in self.AI2.queue:
            if self.button[r][c]["bg"] != 'white':
                self.button[r][c]["bg"] = "green"
        for r,c in self.AI2.known_bombs:
            self.button[r][c]["bg"] = "red"
        for r, c in self.AI2.dirty_tiles:
            self.button[r][c]["bg"] = "orange"

root = Tk()
root.geometry("800x800")

parser = argparse.ArgumentParser()
# parser.add_argument('-f', default = 'deterministic_board.json', type=str, help='the filename (or filepath) of the minesweeper board')
parser.add_argument('-f', default = 'varied_density/20x_20y_18d_3.json', type=str, help='the filename (or filepath) of the minesweeper board')
# parser.add_argument('-f', default = 'undeterministic_board.json', type=str, help='the filename (or filepath) of the minesweeper board')
args = parser.parse_args()

app = Window(testcase_filename = args.f, master = root)

root.mainloop()