from board import Board
from constants import BOARD_HEADER, COMMANDS_HEADER


def parse_input():
    board = []
    commands = []

    reading_board = False
    reading_commands = False

    while True:
        try:
            line = input().strip()
        except EOFError:
            break

        if line == BOARD_HEADER:
            reading_board = True
            continue

        if line == COMMANDS_HEADER:
            reading_board = False
            reading_commands = True
            continue

        if reading_board and line:
            board.append(line.split())
        elif reading_commands and line:
            commands.append(line)
            
            
    return Board(board), commands