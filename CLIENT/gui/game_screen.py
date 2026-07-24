import time

import cv2

from CLIENT.gui.board_mapper import BoardMapper
from CLIENT.network.network_session import NetworkSession
from SHARED.network.protocol import MoveCommand, JumpCommand, GetStateCommand, GameStateUpdated
from CLIENT.network.remote_state import RemoteGameState
from CLIENT.rendering.gui_renderer import GuiRenderer
from CLIENT.gui.image import BOARD_SIDE

WINDOW_NAME = "Chess"
FRAME_DELAY_MS = 16
ESC_KEY = 27


class GameScreen:
    """Network-aware sibling of the local GameWindow: there is no local
    GameEngine here at all - the server is authoritative. Renders whatever
    GameStateUpdated snapshot last arrived over `network`, and turns clicks
    into MoveCommands sent to the server instead of calling a Controller
    directly. `network` is injectable (anything with send()/poll()) so this
    can be tested without a real socket.

    Click handling is deliberately simple: first click selects a square,
    second click sends a move attempt from there - there's no client-side
    legality/ownership check (which color is "mine" isn't even known here),
    the server is the sole arbiter and illegal attempts just don't change
    anything on the next update. Right-clicking the already-selected square
    sends a jump attempt (in place) instead of a move."""

    def __init__(self, username, room_id, my_color=None, server_uri=None, network=None, renderer=None, board_mapper=None):
        self.username = username
        self.room_id = room_id
        self.my_color = my_color
        self.network = network or NetworkSession(server_uri)
        self.renderer = renderer or GuiRenderer()
        self.board_mapper = board_mapper or BoardMapper()
        self.state = None
        self.selected = None

    def run(self):
        self.network.send(GetStateCommand(self.room_id))

        cv2.namedWindow(WINDOW_NAME)
        cv2.setMouseCallback(WINDOW_NAME, self.on_mouse)
        try:
            while True:
                self.poll_network()

                if self.state is not None:
                    canvas = self.renderer.render(self.state, self.selected, time.time(), self.my_color)
                    if not self.show(canvas):
                        break
                else:
                    key = cv2.waitKey(FRAME_DELAY_MS) & 0xFF
                    if key == ESC_KEY:
                        break
        finally:
            cv2.destroyAllWindows()
            self.network.close()

    def poll_network(self):
        response = self.network.poll()
        if isinstance(response, GameStateUpdated) and response.room_id == self.room_id:
            self.state = RemoteGameState(response.state)

    def on_mouse(self, event, x, y, _flags, _param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.handle_click(self.board_mapper.to_position(x, y))
        elif event == cv2.EVENT_RBUTTONDOWN:
            self.handle_right_click(self.board_mapper.to_position(x, y))

    def handle_click(self, position):
        # The window is wider than the board itself (there's a score/move
        # panel to the right of it) - a click out there maps to a column
        # past the board's edge, which must never reach a MoveCommand.
        if not (0 <= position.get_row() < BOARD_SIDE and 0 <= position.get_col() < BOARD_SIDE):
            return

        if self.selected is None:
            self.selected = position
            return

        source = self.selected
        self.selected = None
        self.network.send(MoveCommand(
            self.username, self.room_id,
            (source.get_row(), source.get_col()),
            (position.get_row(), position.get_col()),
        ))

    def handle_right_click(self, position):
        # Jumping only makes sense on the piece you already have selected -
        # a right-click anywhere else (or with nothing selected) is a no-op.
        if self.selected is None or not position.equals(self.selected):
            return

        source = self.selected
        self.selected = None
        self.network.send(JumpCommand(
            self.username, self.room_id,
            (source.get_row(), source.get_col()),
        ))

    def show(self, canvas):
        cv2.imshow(WINDOW_NAME, canvas.img)
        key = cv2.waitKey(FRAME_DELAY_MS) & 0xFF
        if key == ESC_KEY:
            return False
        if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
            return False
        return True
