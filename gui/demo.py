import cv2

from config.constants import CELL_SIZE
from gui.board_layout import load_layout
from gui.image import load_board_image, load_piece_image

ANIMATION_FRAMES = 20
FRAME_DELAY_MS = 16
WINDOW_NAME = "Chess"


def _cell_to_pixel(row, col):
    return col * CELL_SIZE, row * CELL_SIZE


def _draw_static_pieces(board, layout, skip=None):
    for row, cells in enumerate(layout):
        for col, code in enumerate(cells):
            if not code or (row, col) == skip:
                continue
            load_piece_image(code).draw_on(board, *_cell_to_pixel(row, col))


def _animate_move(layout, from_cell, to_cell):
    from_row, from_col = from_cell
    to_row, to_col = to_cell
    code = layout[from_row][from_col]
    piece = load_piece_image(code)

    start_x, start_y = _cell_to_pixel(from_row, from_col)
    end_x, end_y = _cell_to_pixel(to_row, to_col)

    for step in range(1, ANIMATION_FRAMES + 1):
        t = step / ANIMATION_FRAMES
        x = int(start_x + (end_x - start_x) * t)
        y = int(start_y + (end_y - start_y) * t)

        frame = load_board_image()
        _draw_static_pieces(frame, layout, skip=from_cell)
        piece.draw_on(frame, x, y)

        cv2.imshow(WINDOW_NAME, frame.img)
        cv2.waitKey(FRAME_DELAY_MS)

    layout[from_row][from_col] = ""
    layout[to_row][to_col] = code


def run_demo(moves):
    layout = load_layout()
    for from_cell, to_cell in moves:
        _animate_move(layout, from_cell, to_cell)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def _pixel_to_cell(x, y, layout):
    row, col = y // CELL_SIZE, x // CELL_SIZE
    if 0 <= row < len(layout) and 0 <= col < len(layout[0]):
        return row, col
    return None


def run_interactive():
    """No rules, no turns, no captures logic: click a piece, click any
    other square, it moves there - purely to prove mouse-to-board wiring."""
    layout = load_layout()
    state = {"selected": None}

    def on_mouse(event, x, y, _flags, _param):
        if event != cv2.EVENT_LBUTTONDOWN:
            return
        cell = _pixel_to_cell(x, y, layout)
        if cell is None:
            return

        selected = state["selected"]
        row, col = cell
        if selected is None:
            if layout[row][col]:
                state["selected"] = cell
        elif selected == cell:
            state["selected"] = None
        else:
            _animate_move(layout, selected, cell)
            state["selected"] = None

    cv2.namedWindow(WINDOW_NAME)
    cv2.setMouseCallback(WINDOW_NAME, on_mouse)

    while True:
        frame = load_board_image()
        _draw_static_pieces(frame, layout)
        cv2.imshow(WINDOW_NAME, frame.img)

        key = cv2.waitKey(30) & 0xFF
        if key == 27:  # Esc
            break
        if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    run_interactive()
