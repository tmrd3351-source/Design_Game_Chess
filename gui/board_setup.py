from config.constants import EMPTY_CELL
from controller.parser import validate, build_board
from gui.board_layout import load_layout, BOARD_CSV_PATH


def _to_token(code):
    """"RB" (Rook, Black) -> "bR", matching controller.parser's <color><kind>
    token order; the CSV/sprite folders use the opposite <kind><color> order."""
    if not code:
        return EMPTY_CELL
    kind, color = code[0], code[1]
    return f"{color.lower()}{kind.upper()}"


class GuiBoardSetup:
    """Builds the real model.Board from pictures/board.csv - the GUI's
    counterpart to GameSetup, which builds it from the stdin "Board:" text
    instead. Reuses the same validate()/build_board() the CLI path uses."""

    def __init__(self, path=BOARD_CSV_PATH):
        self.path = path

    def load(self):
        layout = load_layout(self.path)
        tokens = [[_to_token(cell) for cell in row] for row in layout]

        error = validate(tokens)
        if error:
            print(error)
            return None

        return build_board(tokens)
