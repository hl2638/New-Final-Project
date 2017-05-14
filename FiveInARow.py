# -*- coding: utf-8 -*-
import os
import pdb
import random
from chat_utils import *

PLAYER_BLACK = False
PLAYER_WHITE = True
F_END = -1


class Five:
    def __init__(self, max_x, max_y):
        self.max_x = max_x
        self.max_y = max_y
        self.board = []
        for i in range(max_x):
            self.board.append([])
            for j in range(max_y):
                self.board[i].append(0)

    def board_init(self, who, from_sock, to_sock):
        self.send_instructions(from_sock, to_sock)
        self.send_board(from_sock, to_sock)
        side = random.choice([0, 1])  # if side = black,
        if side == PLAYER_BLACK:  # (the one who starts the game)-> black; vice versa
            self.black = from_sock
            self.white = to_sock
            self.send_sides(from_sock, to_sock)
        else:
            self.black = to_sock
            self.white = from_sock
            self.send_sides(to_sock, from_sock)
        self.send_direction(who, from_sock, to_sock)  # argument "who" syncs with chat system

    def make_move(self, who, move, from_sock, to_sock):
        t = move

        if t == "q":  # quit the game 
            self.send_result(PLAYER_BLACK if from_sock == self.white else PLAYER_WHITE, from_sock, to_sock)
            self.send_error(to_sock, "Opponent quits.")
            return F_END
        # if white quits, black wins; vice versa

        if (who == PLAYER_BLACK and from_sock == self.white) or (who == PLAYER_WHITE and from_sock == self.black):
            self.send_error(from_sock, "Not your turn yet...")
            return False
        # if the other player tries to play, it won't work

        t = t.strip().split(',')
        try:  # try/except deals with input error (wrong command like 2,100 or 12+,5s)
            x = int(t[0])
            y = int(t[1])

            if self.board[x][y] == 0:
                self.board[x][y] = 1 if who else 2
                # os.system('cls')
                self.send_board(from_sock, to_sock)

                ans = self.isWin(x, y)
                if ans:
                    self.send_result(who, from_sock, to_sock)
                    return F_END  # someone wins; game ends

                self.send_direction(not who, from_sock, to_sock)
                return True  # successful

            else:  # if there is already a piece played on the tile
                self.send_error(from_sock, "Already exists. Try somewhere else!")
                return False

        except:  # wrong command
            self.send_error(from_sock)
            return False
            # os.system('pause')

    def isWin(self, xPoint, yPoint):  # determine if one wins
        # pdb.set_trace
        # flag = False
        t = self.board[xPoint][yPoint]

        # horizontal
        count, x, y = 0, xPoint, yPoint
        while x >= 0 and t == self.board[x][y]:
            count += 1
            x -= 1
        x = xPoint
        while x < self.max_x and t == self.board[x][y]:
            count += 1
            x += 1
        if count > 5:
            return True

        # vertical
        count, x, y = 0, xPoint, yPoint
        while y >= 0 and t == self.board[x][y]:
            count += 1
            y -= 1
        y = yPoint
        while y < self.max_y and t == self.board[x][y]:
            count += 1
            y += 1
        if count > 5:
            return True

        # /
        count, x, y = 0, xPoint, yPoint
        while x >= 0 and y < self.max_y and t == self.board[x][y]:
            count += 1
            x -= 1
            y += 1
        x, y = xPoint, yPoint
        while x < self.max_x and y >= 0 and t == self.board[x][y]:
            count += 1
            x += 1
            y -= 1
        if count > 5:
            return True

        # \
        count, x, y = 0, xPoint, yPoint
        while x >= 0 and y >= 0 and t == self.board[x][y]:
            count += 1
            x -= 1
            y -= 1
        x, y = xPoint, yPoint
        while x < self.max_x and y < self.max_y and t == self.board[x][y]:
            count += 1
            x += 1
            y += 1
        if count > 5:
            return True
        return False

    def printboard(self):  # print the board
        if self.max_y < 11 and self.max_x < 11:  # small board
            result = "    "
            for i in range(self.max_y):
                result += format(str(i), "<2")
            result += "\n"
            for i in range(self.max_x):
                result += format(str(i), ">2")
                for j in range(self.max_y):
                    if self.board[i][j] == 0:
                        result += ' +'
                    elif self.board[i][j] == 1:
                        result += ' o'
                    elif self.board[i][j] == 2:
                        result += ' *'
                result += '\n'
            return result
        else:  # big board
            result = "      "
            for i in range(self.max_y):
                result += format(str(i), "<4")
            result += "\n\n"
            for i in range(self.max_x):
                result += format(str(i), ">2")
                for j in range(self.max_y):
                    if self.board[i][j] == 0:
                        result += '   +'
                    elif self.board[i][j] == 1:
                        result += ' o'
                    elif self.board[i][j] == 2:
                        result += ' *'
                result += "\n\n"
            return result

    def send_board(self, from_sock, to_sock):
        cboard = self.printboard()  # current board
        mysend(from_sock, cboard)
        mysend(to_sock, cboard)

    @staticmethod
    def send_instructions(from_sock, to_sock):
        msg = " Welcome to Five in a Row game.\nInput (x,y) to play a piece on tile (x,y).\n"
        mysend(from_sock, msg)
        mysend(to_sock, msg)

    @staticmethod
    def send_result(who, from_sock, to_sock):
        result = (' WHITE' if who else ' BLACK') + ' Wins'
        mysend(from_sock, result)
        mysend(to_sock, result)

    def send_direction(self, who, from_sock, to_sock):
        if who == PLAYER_WHITE:  # white turn, send to black and white players
            mysend(self.white, " Now it's your turn (o), please input(x,y):")
            mysend(self.black, " Now it's opponent's turn (o):")
        else:  # black turn
            mysend(self.white, " Now it's opponent's turn (*):")
            mysend(self.black, " Now it's your turn (*), please input(x,y):")

    @staticmethod
    def send_sides(black, white):
        mysend(black, ' You are BLACK (*) \n')
        mysend(white, ' You are WHITE (o) \n')

    @staticmethod
    def send_error(to_sock, msg=''):
        if msg == '':  # default message
            mysend(to_sock, ' Error, please try again')
        else:  # can set other messages
            mysend(to_sock, ' ' + msg)
