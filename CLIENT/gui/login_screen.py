import asyncio

import cv2

from CLIENT.network.websocket_client import WebSocketClient
from SHARED.network.protocol import LoginCommand, LoginSucceeded
from CLIENT.rendering.login_renderer import LoginRenderer, USERNAME_FIELD_RECT, PASSWORD_FIELD_RECT, \
    SUBMIT_BUTTON_RECT, REGISTER_LINK_RECT
from CLIENT.rendering.auth_theme import point_in_rect

WINDOW_NAME = "Login"
FRAME_DELAY_MS = 16
NO_KEY = 255
ESC_KEY = 27
ENTER_KEY = 13
TAB_KEY = 9
BACKSPACE_KEY = 8


class _SwitchToRegister:
    """Unique sentinel LoginScreen.run() returns when the user clicks the
    REGISTER link, distinguishable from any real username or a plain None
    (quit) without a fragile magic string that could collide with one."""


SWITCH_TO_REGISTER = _SwitchToRegister()


def _default_login_fn(server_uri):
    """Wraps WebSocketClient's async connect/send/receive into a plain
    synchronous call - login is a one-off action, not part of the real-time
    game loop, so blocking the caller until the response arrives is fine."""

    async def _do_login(username, password):
        client = WebSocketClient(server_uri)
        await client.connect()
        await client.send_command(LoginCommand(username, password))
        response = await client.receive()
        await client.close()
        return response

    return lambda username, password: asyncio.run(_do_login(username, password))


class LoginScreen:
    """Username/password entry. Sends a LoginCommand and shows the result.
    `login_fn(username, password) -> Response` is injectable so the input
    handling and success/failure logic can be tested without a real socket."""

    def __init__(self, server_uri=None, renderer=None, login_fn=None):
        self.renderer = renderer or LoginRenderer()
        self.login_fn = login_fn or _default_login_fn(server_uri)
        self.username = ""
        self.password = ""
        self.active_field = "username"
        self.message = ""
        self.failed_last_attempt = False
        self.logged_in_username = None
        self.switch_to_register = False
        self._should_stop = False

    def run(self):
        """Blocks until login succeeds (returns the username), the user
        clicks REGISTER (returns SWITCH_TO_REGISTER), or the user quits
        (returns None)."""
        cv2.namedWindow(WINDOW_NAME)
        cv2.setMouseCallback(WINDOW_NAME, self._on_mouse)
        try:
            while True:
                self._render()

                key = cv2.waitKey(FRAME_DELAY_MS) & 0xFF
                if self._should_stop:
                    return self._result()
                if key == NO_KEY:
                    continue
                if key == ESC_KEY:
                    return None
                if self.handle_key(key):
                    return self._result()
        finally:
            cv2.destroyWindow(WINDOW_NAME)

    def _render(self):
        canvas = self.renderer.render(self)
        cv2.imshow(WINDOW_NAME, canvas.img)

    def _on_mouse(self, event, x, y, _flags, _param):
        if event == cv2.EVENT_LBUTTONDOWN and self.handle_click(x, y):
            self._should_stop = True

    def _result(self):
        return SWITCH_TO_REGISTER if self.switch_to_register else self.logged_in_username

    def handle_key(self, key):
        """Applies one keypress. Returns True once login has succeeded."""
        if key == TAB_KEY:
            self._switch_field()
        elif key == BACKSPACE_KEY:
            self._backspace()
        elif key == ENTER_KEY:
            return self.submit()
        elif 32 <= key < 127:
            self._type_char(chr(key))
        return False

    def handle_click(self, x, y):
        """Applies one left-click. Returns True once the screen should stop
        running - either login succeeded or the user asked to switch to
        RegisterScreen (see `switch_to_register`)."""
        if point_in_rect(x, y, USERNAME_FIELD_RECT):
            self.active_field = "username"
        elif point_in_rect(x, y, PASSWORD_FIELD_RECT):
            self.active_field = "password"
        elif point_in_rect(x, y, SUBMIT_BUTTON_RECT):
            return self.submit()
        elif point_in_rect(x, y, REGISTER_LINK_RECT):
            self.switch_to_register = True
            return True
        return False

    def _switch_field(self):
        self.active_field = "password" if self.active_field == "username" else "username"

    def _backspace(self):
        if self.active_field == "username":
            self.username = self.username[:-1]
        else:
            self.password = self.password[:-1]

    def _type_char(self, char):
        if self.active_field == "username":
            self.username += char
        else:
            self.password += char

    def submit(self):
        """Sends the current username/password. Returns True on success."""
        if not self.username or not self.password:
            self.message = "Enter both username and password"
            self.failed_last_attempt = True
            return False

        response = self.login_fn(self.username, self.password)

        if isinstance(response, LoginSucceeded):
            self.message = "Login successful"
            self.failed_last_attempt = False
            self.logged_in_username = response.username
            return True

        self.message = f"Login failed: {response.reason}"
        self.failed_last_attempt = True
        return False
