import time

import cv2

from gui.renderer import Renderer

WINDOW_NAME = "Chess"
FRAME_DELAY_MS = 16
GAME_OVER_COLOR = (0, 0, 255, 255)  # BGRA red


def _draw_game_over_overlay(canvas, state):
    if not state.game_over:
        return
    height, width = canvas.img.shape[:2]
    winner_label = "White" if state.winner == "w" else "Black"
    canvas.put_text("GAME OVER", width // 2 - 150, height // 2 - 10,
                     font_size=1.4, color=GAME_OVER_COLOR, thickness=3)
    canvas.put_text(f"{winner_label} wins!", width // 2 - 120, height // 2 + 40,
                     font_size=1.1, color=GAME_OVER_COLOR, thickness=2)


def run_gui_loop(controller, renderer=None):
    """Drives `controller` from real mouse clicks and real elapsed time,
    redrawing every frame. Left click selects/moves, right click jumps.
    GameEngine/RuleEngine/RealTimeArbiter are never touched directly here -
    only through Controller/GameEngine's existing public methods."""
    renderer = renderer or Renderer()

    def on_mouse(event, x, y, _flags, _param):
        if event == cv2.EVENT_LBUTTONDOWN:
            controller.handle_click(x, y)
        elif event == cv2.EVENT_RBUTTONDOWN:
            controller.handle_jump(x, y)

    cv2.namedWindow(WINDOW_NAME)
    cv2.setMouseCallback(WINDOW_NAME, on_mouse)

    last_tick = time.time()
    while True:
        now = time.time()
        elapsed_ms = int((now - last_tick) * 1000)
        last_tick = now

        if elapsed_ms > 0:
            controller.game_engine.wait(elapsed_ms)

        state = controller.get_state()
        canvas = renderer.compose_board(state.board, now)
        _draw_game_over_overlay(canvas, state)
        cv2.imshow(WINDOW_NAME, canvas.img)

        key = cv2.waitKey(FRAME_DELAY_MS) & 0xFF
        if key == 27:  # Esc
            break
        if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
            break

    cv2.destroyAllWindows()
