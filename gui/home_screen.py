import cv2

from network.network_session import NetworkSession
from network.protocol import PlayCommand, Waiting, GameStarted
from rendering.home_renderer import HomeRenderer

WINDOW_NAME = "Home"
FRAME_DELAY_MS = 16
NO_KEY = 255
ESC_KEY = 27


def _default_network(server_uri):
    return NetworkSession(server_uri)


class HomeScreen:
    """Shown after a successful login. Play sends a PlayCommand and then
    waits (polled once per frame, never blocking the render loop) for
    either Waiting or a later GameStarted push. Create/Join Room aren't
    wired to anything yet - this only proves the
    Login -> Home -> Play -> Waiting -> Game Started flow; connecting the
    actual chessboard once a game starts is a separate step.

    `network` is injectable (anything with send()/poll()) so this can be
    tested without a real socket."""

    def __init__(self, username, server_uri=None, network=None, renderer=None):
        self.username = username
        self.network = network or _default_network(server_uri)
        self.renderer = renderer or HomeRenderer()
        self.status = "idle"  # idle | waiting | started
        self.message = ""
        self.room_id = None

    def run(self):
        """Blocks until a game starts (returns the room_id) or the user
        quits (returns None)."""
        cv2.namedWindow(WINDOW_NAME)
        try:
            while True:
                self.poll_network()
                # Checked right after polling, independent of any keypress -
                # a match can arrive as an unsolicited push on a frame where
                # the user presses nothing at all.
                if self.status == "started":
                    return self.room_id

                self._render()
                key = cv2.waitKey(FRAME_DELAY_MS) & 0xFF
                if key == ESC_KEY:
                    return None
                if key != NO_KEY:
                    self.handle_key(key)
        finally:
            cv2.destroyWindow(WINDOW_NAME)

    def _render(self):
        canvas = self.renderer.render(self)
        cv2.imshow(WINDOW_NAME, canvas.img)

    def poll_network(self):
        """Checks for one pending server message, if any. Safe to call every
        frame - non-blocking when nothing has arrived."""
        response = self.network.poll()
        if response is not None:
            self._handle_response(response)

    def handle_key(self, key):
        """Applies one keypress. Returns True once a game has started."""
        char = chr(key).lower()
        if char == "p":
            self.play()
        elif char == "c":
            self.message = "Create Room isn't wired up yet"
        elif char == "j":
            self.message = "Join Room isn't wired up yet"
        return self.status == "started"

    def play(self):
        self.network.send(PlayCommand(self.username))
        self.status = "waiting"
        self.message = "Waiting for an opponent..."

    def _handle_response(self, response):
        if isinstance(response, Waiting):
            self.status = "waiting"
            self.message = "Waiting for an opponent..."
        elif isinstance(response, GameStarted):
            self.status = "started"
            self.room_id = response.room_id
            self.message = f"Game started! Room: {response.room_id}"
