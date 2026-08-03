from SERVER.config.constants import BOARD_HEADER, COMMANDS_HEADER, EMPTY_CELL, VALID_TOKENS
from SERVER.engine.model.board import Board
from SERVER.engine.model.piece import Piece
from SERVER.engine.model.position import Position


def parse_input():
    tokens = []
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
            tokens.append(line.split())
        elif reading_commands and line:
            commands.append(line)

    return tokens, commands


def validate(tokens):
    if not tokens:
        return None

    width = len(tokens[0])
    for row in tokens:
        if len(row) != width:
            return "ERROR ROW_WIDTH_MISMATCH"

        for token in row:
            if token not in VALID_TOKENS:
                return "ERROR UNKNOWN_TOKEN"

    return None


def build_board(tokens):
    rows = len(tokens)
    cols = len(tokens[0]) if rows else 0
    board = Board(rows, cols)

    next_id = 0
    for row in range(rows):
        for col in range(cols):
            token = tokens[row][col]
            if token == EMPTY_CELL:
                continue
            piece = Piece(next_id, token[0], token[1], Position(row, col))
            next_id += 1
            board.add_piece(piece)

    return board
