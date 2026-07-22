import asyncio

import cv2

from CLIENT.network.websocket_client import WebSocketClient
from SHARED.network.protocol import RegisterCommand, RegisterSucceeded
from CLIENT.rendering.register_renderer import RegisterRenderer, USERNAME_FIELD_RECT, PASSWORD_FIELD_RECT, \
    CONFIRM_FIELD_RECT, SUBMIT_BUTTON_RECT, LOGIN_LINK_RECT
from CLIENT.rendering.auth_theme import point_in_rect

WINDOW_NAME = "Register"
FRAME_DELAY_MS = 16
NO_KEY = 255
ESC_KEY = 27
ENTER_KEY = 13
TAB_KEY = 9
BACKSPACE_KEY = 8

_FIELD_ORDER = ("username", "password", "confirm_password")


class _SwitchToLogin:
    """Unique sentinel RegisterScreen.run() returns when the user clicks the
    LOG IN link, distinguishable from any real username or a plain None
    (quit) without a fragile magic string that could collide with one."""


SWITCH_TO_LOGIN = _SwitchToLogin()


def _default_register_fn(server_uri):
    """Mirrors login_screen's _default_login_fn: registration is a one-off
    action, not part of the real-time game loop, so blocking the caller
    until the response arrives is fine."""

    async def _do_register(username, password):
        client = WebSocketClient(server_uri)
        await client.connect()
        await client.send_command(RegisterCommand(username, password))
        response = await client.receive()
        await client.close()
        return response

    return lambda username, password: asyncio.run(_do_register(username, password))


class RegisterScreen:
    """Username/password/confirm-password entry. Sends a RegisterCommand
    and, on success, treats the caller as logged in immediately (the client
    just sent these exact credentials to create the account, so there's no
    reason to make them retype them into LoginScreen).
    `register_fn(username, password) -> Response` is injectable so the input
    handling and success/failure logic can be tested without a real socket."""

    def __init__(self, server_uri=None, renderer=None, register_fn=None):
        self.renderer = renderer or RegisterRenderer()
        self.register_fn = register_fn or _default_register_fn(server_uri)
        self.username = ""
        self.password = ""
        self.confirm_password = ""
        self.active_field = "username"
        self.message = ""
        self.failed_last_attempt = False
        self.logged_in_username = None
        self.switch_to_login = False
        self._should_stop = False

    def run(self):
        """Blocks until registration succeeds (returns the username), the
        user clicks LOG IN (returns SWITCH_TO_LOGIN), or the user quits
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
        return SWITCH_TO_LOGIN if self.switch_to_login else self.logged_in_username

    def handle_key(self, key):
        """Applies one keypress. Returns True once registration has
        succeeded."""
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
        running - either registration succeeded or the user asked to switch
        to LoginScreen (see `switch_to_login`)."""
        if point_in_rect(x, y, USERNAME_FIELD_RECT):
            self.active_field = "username"
        elif point_in_rect(x, y, PASSWORD_FIELD_RECT):
            self.active_field = "password"
        elif point_in_rect(x, y, CONFIRM_FIELD_RECT):
            self.active_field = "confirm_password"
        elif point_in_rect(x, y, SUBMIT_BUTTON_RECT):
            return self.submit()
        elif point_in_rect(x, y, LOGIN_LINK_RECT):
            self.switch_to_login = True
            return True
        return False

    def _switch_field(self):
        index = _FIELD_ORDER.index(self.active_field)
        self.active_field = _FIELD_ORDER[(index + 1) % len(_FIELD_ORDER)]

    def _backspace(self):
        setattr(self, self.active_field, getattr(self, self.active_field)[:-1])

    def _type_char(self, char):
        setattr(self, self.active_field, getattr(self, self.active_field) + char)

    def submit(self):
        """Sends the current username/password. Returns True on success."""
        if not self.username or not self.password:
            self.message = "Enter both username and password"
            self.failed_last_attempt = True
            return False

        if self.password != self.confirm_password:
            self.message = "Passwords do not match"
            self.failed_last_attempt = True
            return False

        response = self.register_fn(self.username, self.password)

        if isinstance(response, RegisterSucceeded):
            self.message = "Account created"
            self.failed_last_attempt = False
            self.logged_in_username = response.username
            return True

        self.message = f"Registration failed: {response.reason}"
        self.failed_last_attempt = True
        return False
