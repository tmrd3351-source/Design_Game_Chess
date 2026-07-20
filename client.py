from gui.login_screen import LoginScreen
from gui.home_screen import HomeScreen

SERVER_URI = "ws://localhost:8765"


def main():
    """Composition root for the visual client: Login -> Home. Connecting the
    actual chessboard once a game starts isn't wired up yet."""
    # login = LoginScreen(server_uri=SERVER_URI)
    # username = login.run()
    # if username is None:
    #     return

    home = HomeScreen("alice", server_uri=SERVER_URI)
    room_id = home.run()
    if room_id is not None:
        print(f"Game started in room {room_id} - board rendering isn't wired up yet.")


if __name__ == "__main__":
    main()
