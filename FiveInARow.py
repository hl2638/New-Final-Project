# -*- coding: utf-8 -*-
import os
import pdb
from chat_utils import *


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
        self.send_board(from_sock, to_sock)
        self.send_direction(who, from_sock, to_sock)

    def make_move(self, who, move, from_sock, to_sock):
        t = move
        if t == "q":  # quit the game
            self.send_result(who, from_sock, to_sock)
        t = t.split(',')
        if len(t) == 2:
            x = int(t[0])
            y = int(t[1])
            if self.board[x][y] == 0:
                self.board[x][y] = 1 if who else 2
                # os.system('cls')
                self.send_board(from_sock, to_sock)
                ans = self.isWin(x, y)
                if ans:
                    self.send_result(who, from_sock, to_sock)
        self.send_direction(not who, from_sock, to_sock)
        # os.system('pause')

    def isWin(self, xPoint, yPoint):  # determine if one wins
        # pdb.set_trace
        # flag = False
        t = self.board[xPoint][yPoint]

        # horizontal
        count, x, y = 0, xPoint, yPoint
        while x > 0 and t == self.board[x][y]:
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
        while y > 0 and t == self.board[x][y]:
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
        while x > 0 and y < self.max_y and t == self.board[x][y]:
            count += 1
            x -= 1
            y += 1
        x, y = xPoint, yPoint
        while x < self.max_x and y > 0 and t == self.board[x][y]:
            count += 1
            x += 1
            y -= 1
        if count > 5:
            return True

        # \
        count, x, y = 0, xPoint, yPoint
        while x > 0 and y > 0 and t == self.board[x][y]:
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
        '''print(' 〇一二三四五六七八九')
        for i in range(self.max_x):
            print(i, end='')
            for j in range(self.max_y):
                if self.board[i][j] == 0:
                    print('十', end='')
                elif self.board[i][j] == 1:
                    print('〇', end='')
                elif self.board[i][j] == 2:
                    print('●', end='')
            print('\n')'''
        result = '   0 1 2 3 4 5 6 7 8 9\n'
        for i in range(self.max_x):
            result += str(i)
            for j in range(self.max_y):
                if self.board[i][j] == 0:
                    # result += '十'
                    result += ' +'
                elif self.board[i][j] == 1:
                    result += ' o'
                elif self.board[i][j] == 2:
                    result += ' *'
            result += '\n'
        return result

    def send_board(self, from_sock, to_sock):
        cboard = self.printboard()  # current board
        mysend(from_sock, cboard)
        mysend(to_sock, cboard)

    @staticmethod
    def send_result(who, from_sock, to_sock):
        result = ('o' if who else '*') + 'Wins'
        mysend(from_sock, result)
        mysend(to_sock, result)

    @staticmethod
    def send_direction(who, from_sock, to_sock):
        mysend(from_sock, ' Please input(x,y),now is ' + ('o' if who else '*') + ':')
        mysend(to_sock, ' Please input(x,y),now is ' + ('o' if who else '*') + ':')


def game_init():
    return Five(10, 10)
    # pdb.set_trace()


def start(move, from_sock, to_sock):
    game.make_move(move, from_sock, to_sock)


