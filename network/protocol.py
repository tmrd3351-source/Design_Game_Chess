# The wire protocol between client and server: Commands travel client -> server,
# Responses travel server -> client. Deliberately plain data holders - no
# behavior, no transport - so the same shapes work whether they're carried by
# a fake in-process call or a real serialized WebSocket message later.


class LoginCommand:
    def __init__(self, username, password):
        self.username = username
        self.password = password


class PlayCommand:
    def __init__(self, username):
        self.username = username


class CreateRoomCommand:
    def __init__(self, username):
        self.username = username


class JoinRoomCommand:
    def __init__(self, username, room_id):
        self.username = username
        self.room_id = room_id


class MoveCommand:
    def __init__(self, username, room_id, source, destination):
        self.username = username
        self.room_id = room_id
        self.source = source  # (row, col)
        self.destination = destination  # (row, col)


class LoginSucceeded:
    def __init__(self, username):
        self.username = username


class LoginFailed:
    def __init__(self, reason):
        self.reason = reason


class RoomCreated:
    def __init__(self, room_id):
        self.room_id = room_id


class GameStarted:
    def __init__(self, room_id):
        self.room_id = room_id


class GameStateUpdated:
    def __init__(self, room_id, state):
        self.room_id = room_id
        self.state = state


class Waiting:
    """Sent when PlayCommand found no compatible opponent yet - the caller
    stays in the Matchmaker's queue until someone else matches them."""
