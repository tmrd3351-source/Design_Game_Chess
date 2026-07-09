from constants import CELL_SIZE, COMMAND_PRINT_BOARD, COMMAND_WAIT, COMMAND_CLICK, EMPTY_CELL, MOVE_TIME
from move_rules import is_move_legal


class Game:

    def __init__(self, board):
        self.board = board
        self.time = 0
        self.selected = None
        self.pending_moves = []

    def apply_command(self, command):
        if command == COMMAND_PRINT_BOARD:
            self.print_board()
            return

        tokens = command.split()
        if not tokens:
            return

        verb = tokens[0]
        if verb == COMMAND_WAIT and len(tokens) == 2:
            self.wait(int(tokens[1]))
            return

        if verb == COMMAND_CLICK and len(tokens) == 3:
            self.click(int(tokens[1]), int(tokens[2]))

    def click(self, x, y):
        row = y // CELL_SIZE
        col = x // CELL_SIZE

        if not self.board.inside_board(row, col):
            return

        piece = self.board.get_cell(row, col)

        if self.selected is None:
            if piece != EMPTY_CELL and not self._is_moving(row, col):
                self.selected = (row, col)
            return

        old_row, old_col = self.selected
        old_piece = self.board.get_cell(old_row, old_col)

        if piece != EMPTY_CELL and piece[0] == old_piece[0]:
            if not self._is_moving(row, col):
                self.selected = (row, col)
            else:
                self.selected = None
            return

        if is_move_legal(self.board, old_row, old_col, row, col):
            self.pending_moves.append({
                "r1": old_row,
                "c1": old_col,
                "r2": row,
                "c2": col,
                "arrival": self.time + MOVE_TIME,
            })

        self.selected = None

    def _is_moving(self, row, col):
        return any(move["r1"] == row and move["c1"] == col for move in self.pending_moves)

    def _resolve_pending_moves(self):
        still_pending = []
        for move in self.pending_moves:
            if self.time >= move["arrival"]:
                self.board.move_piece(move["r1"], move["c1"], move["r2"], move["c2"])
            else:
                still_pending.append(move)
        self.pending_moves = still_pending

    def wait(self, ms):
        self.time += ms
        self._resolve_pending_moves()

    def print_board(self):
        self._resolve_pending_moves()
        self.board.print_board()

