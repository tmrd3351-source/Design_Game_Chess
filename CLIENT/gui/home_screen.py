import cv2

from CLIENT.network.network_session import NetworkSession
from SHARED.network.protocol import (
    PlayCommand, CreateRoomCommand, JoinRoomCommand, CheckReconnectCommand,
    Waiting, GameStarted, PlayFailed, RoomCreated, RoomJoined, RoomJoinFailed,
    ReconnectAvailable, NoReconnectAvailable,
)
from CLIENT.rendering.home_renderer import HomeRenderer

WINDOW_NAME = "Home"
FRAME_DELAY_MS = 16
NO_KEY = 255
ESC_KEY = 27
ENTER_KEY = 13
BACKSPACE_KEY = 8


def _default_network(server_uri):
    return NetworkSession(server_uri)


class HomeScreen:
    """Shown after a successful login. Play sends a PlayCommand and then
    waits (polled once per frame, never blocking the render loop) for
    either Waiting or a later GameStarted push. Create Room sends a
    CreateRoomCommand right away and waits the same way for someone else to
    join. Join Room first collects a room ID typed on-screen (status
    "entering_room_id"), then sends a JoinRoomCommand once Enter is
    pressed. This only proves the
    Login -> Home -> Play/Create/Join -> Waiting -> Game Started flow;
    connecting the actual chessboard once a game starts is a separate step.

    On startup, also sends a CheckReconnectCommand - if this username was
    seated in a game whose connection dropped and is still within its
    grace period, the player is offered to rejoin it (status
    "reconnect_prompt") before the normal menu is even shown.

    `network` is injectable (anything with send()/poll()) so this can be
    tested without a real socket."""

    def __init__(self, username, server_uri=None, network=None, renderer=None):
        self.username = username
        self.network = network or _default_network(server_uri)
        self.renderer = renderer or HomeRenderer()
        self.status = "idle"  # idle | waiting | entering_room_id | reconnect_prompt | started
        self.message = ""
        self.room_id = None
        self.color = None
        self.room_id_input = ""

    def run(self):
        """Blocks until a game starts (returns the room_id) or the user
        quits (returns None). The connection is only closed on the quit
        path - when a game starts, the caller is expected to hand this same
        `network` to GameScreen rather than opening a second connection, so
        the server never sees this player as having disconnected mid-game."""
        self.check_reconnect()
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
                    self.network.close()
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
        if self.status == "entering_room_id":
            self._handle_room_id_key(key)
            return self.status == "started"
        if self.status == "reconnect_prompt":
            self._handle_reconnect_prompt_key(key)
            return self.status == "started"

        char = chr(key).lower()
        if char == "p":
            self.play()
        elif char == "c":
            self.create_room()
        elif char == "j":
            self.status = "entering_room_id"
            self.room_id_input = ""
            self.message = "Enter room ID, then press Enter"
        return self.status == "started"

    def _handle_room_id_key(self, key):
        if key == ENTER_KEY:
            if self.room_id_input:
                self.join_room(self.room_id_input)
        elif key == BACKSPACE_KEY:
            self.room_id_input = self.room_id_input[:-1]
        elif 32 <= key < 127:
            self.room_id_input += chr(key).lower()

    def _handle_reconnect_prompt_key(self, key):
        char = chr(key).lower()
        if char == "y":
            self.join_room(self.room_id)
        elif char == "n":
            self.status = "idle"
            self.message = ""

    def check_reconnect(self):
        self.network.send(CheckReconnectCommand(self.username))

    def play(self):
        self.network.send(PlayCommand(self.username))
        self.status = "waiting"
        self.message = "Waiting for an opponent..."

    def create_room(self):
        self.network.send(CreateRoomCommand(self.username))
        self.status = "waiting"
        self.message = "Creating room..."

    def join_room(self, room_id):
        self.network.send(JoinRoomCommand(self.username, room_id))
        self.status = "waiting"
        self.message = f"Joining room {room_id}..."

    def _handle_response(self, response):
        if isinstance(response, Waiting):
            self.status = "waiting"
            self.message = "Waiting for an opponent..."
        elif isinstance(response, GameStarted):
            self.status = "started"
            self.room_id = response.room_id
            self.color = response.color
            self.message = f"Game started! Room: {response.room_id}"
        elif isinstance(response, PlayFailed):
            self.status = "idle"
            self.message = f"Couldn't play: {response.reason}"
        elif isinstance(response, RoomCreated):
            self.status = "waiting"
            self.room_id = response.room_id
            self.color = response.color
            self.message = f"Room created! Share this ID: {response.room_id}"
        elif isinstance(response, RoomJoined):
            self.status = "started"
            self.room_id = response.room_id
            self.color = response.color
            self.message = f"Game started! Room: {response.room_id}"
        elif isinstance(response, RoomJoinFailed):
            self.status = "idle"
            self.message = f"Couldn't join room: {response.reason}"
        elif isinstance(response, ReconnectAvailable):
            self.status = "reconnect_prompt"
            self.room_id = response.room_id
            self.color = response.color
            self.message = f"You have an active game in room {response.room_id}. Reconnect? [Y/N]"
        elif isinstance(response, NoReconnectAvailable):
            pass  # nothing to offer - stay on the normal menu
