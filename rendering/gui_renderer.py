import time

from config.constants import CELL_SIZE, REST_NONE, MOTION_TRANSLATE
from model.position import Position
from rendering.animation_manager import AnimationManager
from gui.image import load_board_image

REST_OVERLAY_COLOR = (0, 210, 255)  # BGR - semi-transparent yellow
REST_OVERLAY_ALPHA = 0.45

SELECTION_OVERLAY_COLOR = (0, 220, 0)  # BGR - semi-transparent green
SELECTION_OVERLAY_ALPHA = 0.35

GAME_OVER_COLOR = (0, 0, 255, 255)  # BGRA red


def _sprite_code(piece):
    """model.Piece -> sprite folder code, e.g. color="w", kind="R" -> "RW"
    (pictures/ uses <kind><color> order, the opposite of engine tokens)."""
    return f"{piece.get_kind()}{piece.get_color().upper()}"


class GuiRenderer:

    def __init__(self, animation_manager=None):
        self.animation_manager = animation_manager or AnimationManager()

    def render(self, game_state, selected=None, now=None):
        now = time.time() if now is None else now
        canvas = self.draw_board()
        self.draw_pieces(canvas, game_state.board, game_state.motions, now)
        self.draw_motion(canvas, game_state.motions, now)
        self.draw_selection(canvas, selected)
        self.draw_cooldown(canvas, game_state.board)
        self.draw_game_over(canvas, game_state)
        return canvas

    def draw_board(self):
        return load_board_image()

    def draw_pieces(self, canvas, board, motions, now):
        # Pieces mid-translate still sit at their origin cell in the board
        # grid (it's only updated once the whole route lands), so they're
        # skipped here and drawn by draw_motion instead - otherwise they'd
        # be painted twice, once static and once sliding.
        moving_pieces = {motion.piece for motion in motions if motion.kind == MOTION_TRANSLATE}
        for row in range(board.rows):
            for col in range(board.cols):
                piece = board.get_piece(Position(row, col))
                if piece is None or piece in moving_pieces:
                    continue
                frame = self.animation_manager.get_frame(piece, _sprite_code(piece), now)
                frame.draw_on(canvas, col * CELL_SIZE, row * CELL_SIZE)

    def draw_selection(self, canvas, selected):
        if selected is None:
            return
        canvas.draw_overlay_rect(
            selected.get_col() * CELL_SIZE, selected.get_row() * CELL_SIZE,
            CELL_SIZE, CELL_SIZE, SELECTION_OVERLAY_COLOR, SELECTION_OVERLAY_ALPHA,
        )

    def draw_motion(self, canvas, motions, now):
        for motion in motions:
            if motion.kind != MOTION_TRANSLATE:
                continue
            start_x, start_y = motion.source.get_col() * CELL_SIZE, motion.source.get_row() * CELL_SIZE
            end_x, end_y = motion.destination.get_col() * CELL_SIZE, motion.destination.get_row() * CELL_SIZE
            x = int(start_x + (end_x - start_x) * motion.progress)
            y = int(start_y + (end_y - start_y) * motion.progress)
            frame = self.animation_manager.get_frame(motion.piece, _sprite_code(motion.piece), now)
            frame.draw_on(canvas, x, y)

    def draw_cooldown(self, canvas, board):
        for row in range(board.rows):
            for col in range(board.cols):
                piece = board.get_piece(Position(row, col))
                if piece is None or piece.get_rest_type() == REST_NONE:
                    continue
                remaining = 1.0 - piece.get_rest_progress()
                height = int(remaining * CELL_SIZE)
                canvas.draw_overlay_rect(
                    col * CELL_SIZE, row * CELL_SIZE + (CELL_SIZE - height),
                    CELL_SIZE, height, REST_OVERLAY_COLOR, REST_OVERLAY_ALPHA,
                )

    def draw_game_over(self, canvas, game_state):
        if not game_state.game_over:
            return
        height, width = canvas.img.shape[:2]
        winner_label = "White" if game_state.winner == "w" else "Black"
        canvas.put_text("GAME OVER", width // 2 - 150, height // 2 - 10,
                         font_size=1.4, color=GAME_OVER_COLOR, thickness=3)
        canvas.put_text(f"{winner_label} wins!", width // 2 - 120, height // 2 + 40,
                         font_size=1.1, color=GAME_OVER_COLOR, thickness=2)


if __name__ == "__main__":
    from setup.board_setup import GuiBoardSetup
    from model.game_state import GameState

    board = GuiBoardSetup().load()
    if board is not None:
        GuiRenderer().render(GameState(board, winner=None, game_over=False)).show()
