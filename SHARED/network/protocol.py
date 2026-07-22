# The wire protocol between client and server: Commands travel client -> server,
# Responses travel server -> client. Deliberately plain data holders - no
# behavior, no transport - so the same shapes work whether they're carried by
# a fake in-process call or a real serialized WebSocket message later.


class LoginCommand:
    def __init__(self, username, password):
        self.username = username
        self.password = password


class RegisterCommand:
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


class GetStateCommand:
    """Fetches the current GameStateUpdated for a room without joining it -
    for a spectator who was never seated, JoinRoomCommand would add them as
    one instead of just reading the board."""

    def __init__(self, room_id):
        self.room_id = room_id


class CheckReconnectCommand:
    """Sent right after connecting so the server can say whether this
    username is mid-grace-period on a game whose connection just dropped -
    if so, the client offers to rejoin it instead of going to the normal
    Home screen."""

    def __init__(self, username):
        self.username = username


class LoginSucceeded:
    def __init__(self, username):
        self.username = username


class LoginFailed:
    def __init__(self, reason):
        self.reason = reason


class RegisterSucceeded:
    def __init__(self, username):
        self.username = username


class RegisterFailed:
    def __init__(self, reason):
        self.reason = reason


class RoomCreated:
    def __init__(self, room_id, color=None):
        self.room_id = room_id
        self.color = color


class RoomJoined:
    """The direct reply to a successful JoinRoomCommand - and also what the
    room's creator is pushed once someone else joins, so both sides learn
    their own color the same way GameStarted does for matchmaking."""

    def __init__(self, room_id, color, state):
        self.room_id = room_id
        self.color = color
        self.state = state


class RoomJoinFailed:
    def __init__(self, reason):
        self.reason = reason


class GameStarted:
    def __init__(self, room_id, color=None):
        self.room_id = room_id
        self.color = color


class GameStateUpdated:
    def __init__(self, room_id, state):
        self.room_id = room_id
        self.state = state


class Waiting:
    """Sent when PlayCommand found no compatible opponent yet - the caller
    stays in the Matchmaker's queue until someone else matches them."""


class PlayFailed:
    def __init__(self, reason):
        self.reason = reason


class ReconnectAvailable:
    def __init__(self, room_id, color):
        self.room_id = room_id
        self.color = color


class NoReconnectAvailable:
    """Sent when CheckReconnectCommand finds no pending disconnected game
    for this username."""
