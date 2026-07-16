import time

from config.constants import CELL_SIZE
from model.position import Position
from model.piece import REST_NONE
from gui.animation_manager import AnimationManager
from gui.image import load_board_image

REST_OVERLAY_COLOR = (0, 210, 255)  # BGR - semi-transparent yellow
REST_OVERLAY_ALPHA = 0.45


def _sprite_code(piece):
    """model.Piece -> sprite folder code, e.g. color="w", kind="R" -> "RW"
    (pictures/ uses <kind><color> order, the opposite of engine tokens)."""
    return f"{piece.get_kind()}{piece.get_color().upper()}"


class Renderer:

    def __init__(self, animation_manager=None):
        self.animation_manager = animation_manager or AnimationManager()

    def render(self, board, now=None):
        self.compose_board(board, now).show()

    def compose_board(self, board, now=None):
        now = time.time() if now is None else now
        canvas = load_board_image()
        for row in range(board.rows):
            for col in range(board.cols):
                piece = board.get_piece(Position(row, col))
                if piece is None:
                    continue
                frame = self.animation_manager.get_frame(piece, _sprite_code(piece), now)
                frame.draw_on(canvas, col * CELL_SIZE, row * CELL_SIZE)
                self._draw_rest_overlay(canvas, piece, row, col)
        return canvas

    @staticmethod
    def _draw_rest_overlay(canvas, piece, row, col):
        if piece.get_rest_type() == REST_NONE:
            return
        remaining = 1.0 - piece.get_rest_progress()
        height = int(remaining * CELL_SIZE)
        canvas.draw_overlay_rect(
            col * CELL_SIZE, row * CELL_SIZE + (CELL_SIZE - height),
            CELL_SIZE, height, REST_OVERLAY_COLOR, REST_OVERLAY_ALPHA,
        )


if __name__ == "__main__":
    from gui.board_setup import GuiBoardSetup

    board = GuiBoardSetup().load()
    if board is not None:
        Renderer().render(board)
