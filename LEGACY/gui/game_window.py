import time

import cv2

from CLIENT.rendering.gui_renderer import GuiRenderer

WINDOW_NAME = "Chess"
FRAME_DELAY_MS = 16
ESC_KEY = 27


class GameWindow:
    """Drives `controller` from real mouse clicks and real elapsed time,
    redrawing every frame. Left click selects/moves, right click jumps.
    GameEngine/RuleEngine/RealTimeArbiter are never touched directly here -
    only through Controller's public methods."""

    def __init__(self, controller, renderer=None):
        self.controller = controller
        self.renderer = renderer or GuiRenderer()

    def run(self):
        cv2.namedWindow(WINDOW_NAME)
        cv2.setMouseCallback(WINDOW_NAME, self.on_mouse)

        last_tick = time.time()
        while True:
            now = time.time()
            elapsed_ms = int((now - last_tick) * 1000)
            last_tick = now

            if elapsed_ms > 0:
                self.controller.handle_wait(elapsed_ms)

            state = self.controller.get_state()
            canvas = self.renderer.render(state, self.controller.selected, now)
            if not self.show(canvas):
                break

        cv2.destroyAllWindows()

    def on_mouse(self, event, x, y, _flags, _param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.controller.handle_click(x, y)
        elif event == cv2.EVENT_RBUTTONDOWN:
            self.controller.handle_jump(x, y)

    def show(self, canvas):
        cv2.imshow(WINDOW_NAME, canvas.img)
        key = cv2.waitKey(FRAME_DELAY_MS) & 0xFF
        if key == ESC_KEY:
            return False
        if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
            return False
        return True
