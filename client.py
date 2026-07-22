from CLIENT.gui.login_screen import LoginScreen, SWITCH_TO_REGISTER
from CLIENT.gui.register_screen import RegisterScreen, SWITCH_TO_LOGIN
from CLIENT.gui.home_screen import HomeScreen
from CLIENT.gui.game_screen import GameScreen

SERVER_URI = "ws://localhost:8765"


def _authenticate():
    """Drives LoginScreen/RegisterScreen, following the link between them
    until one returns a real username (signed in or just registered) or the
    user quits."""
    screen = LoginScreen(server_uri=SERVER_URI)
    while True:
        result = screen.run()
        if result is SWITCH_TO_REGISTER:
            screen = RegisterScreen(server_uri=SERVER_URI)
        elif result is SWITCH_TO_LOGIN:
            screen = LoginScreen(server_uri=SERVER_URI)
        else:
            return result


def main():
    """Composition root for the visual client: Login/Register -> Home ->
    board."""
    username = _authenticate()
    if username is None:
        return

    home = HomeScreen(username, server_uri=SERVER_URI)
    room_id = home.run()
    if room_id is None:
        return

    game = GameScreen(username, room_id, home.color, network=home.network)
    game.run()


if __name__ == "__main__":
    main()
