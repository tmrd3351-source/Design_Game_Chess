from config.constants import EMPTY_CELL
from model.position import Position


class CliRenderer:

    def render(self, board):
        for row in range(board.rows):
            cells = [self._token(board.get_piece(Position(row, col))) for col in range(board.cols)]
            print(" ".join(cells))

    def _token(self, piece):
        if piece is None:
            return EMPTY_CELL
        return piece.get_color() + piece.get_kind()
