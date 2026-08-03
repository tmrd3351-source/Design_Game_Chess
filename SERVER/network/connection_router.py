from SERVER.engine.model.position import Position
from SERVER.network.network_publisher import NetworkPublisher
from SHARED.network.protocol import (
    LoginCommand, RegisterCommand, PlayCommand, CreateRoomCommand, JoinRoomCommand, MoveCommand, JumpCommand,
    GetStateCommand, CheckReconnectCommand, LoginSucceeded, LoginFailed, RegisterSucceeded, RegisterFailed,
    GameStarted, Waiting, PlayFailed, RoomCreated, RoomJoined, RoomJoinFailed, GameStateUpdated,
    ReconnectAvailable, NoReconnectAvailable,
)


class ConnectionRouter:
    """Dispatches an incoming protocol Command to the right GameSession and
    publishes the protocol Response through `publisher` - never returns
    anything itself. `publisher` is a transport-agnostic object exposing
    unicast(username, response) (one connection) and broadcast(room_id,
    response) (every connection in a room); WebSocketServer is the real one,
    wiring itself in as `router.publisher = self` once both exist.

    Also the sole place that wires a NetworkPublisher onto a session - always
    the moment that session is created (or first reached), so it's already
    subscribed before any later join can fill the second seat and fire
    GAME_STARTED on the session's own EventBus."""

    def __init__(self, game_manager, auth_service, matchmaker, publisher=None):
        self.game_manager = game_manager
        self.auth_service = auth_service
        self.matchmaker = matchmaker
        self.publisher = publisher
        self._wired_rooms = set()
        self._handlers = {
            LoginCommand: self._handle_login,
            RegisterCommand: self._handle_register,
            PlayCommand: self._handle_play,
            CreateRoomCommand: self._handle_create_room,
            JoinRoomCommand: self._handle_join_room,
            MoveCommand: self._handle_move,
            JumpCommand: self._handle_jump,
            GetStateCommand: self._handle_get_state,
            CheckReconnectCommand: self._handle_check_reconnect,
        }

    def handle(self, command):
        handler = self._handlers.get(type(command))
        if handler is None:
            return None
        handler(command)
        return None

    def _ensure_publisher(self, session):
        if session.room_id in self._wired_rooms:
            return
        self._wired_rooms.add(session.room_id)
        NetworkPublisher(
            session,
            broadcast=lambda response: self.publisher.broadcast(session.room_id, response),
            unicast=self.publisher.unicast,
        )

    def _handle_login(self, command):
        user = self.auth_service.login(command.username, command.password)
        if user is None:
            self.publisher.unicast(command.username, LoginFailed("invalid_credentials"))
            return
        self.publisher.unicast(user.username, LoginSucceeded(user.username))

    def _handle_register(self, command):
        user = self.auth_service.register(command.username, command.password)
        if user is None:
            self.publisher.unicast(command.username, RegisterFailed("username_taken"))
            return
        self.publisher.unicast(user.username, RegisterSucceeded(user.username))

    def _handle_play(self, command):
        user = self.auth_service.get_user(command.username)
        if user is None:
            self.publisher.unicast(command.username, PlayFailed("unknown_user"))
            return
        session = self.matchmaker.find_match(command.username, user.rating)
        if session is None:
            self.publisher.unicast(command.username, Waiting())
            return

        # The room is brand new here and both players are already seated -
        # Matchmaker.find_match() seats them synchronously before returning,
        # so GAME_STARTED already fired on the session's EventBus before a
        # NetworkPublisher could ever be wired to catch it. Notifying every
        # seated player directly is the only way either of them (matched
        # caller or already-waiting opponent) learns their color.
        self._ensure_publisher(session)
        for username in session.players.values():
            self.publisher.unicast(username, GameStarted(session.room_id, session.color_of(username)))

    def _handle_create_room(self, command):
        session = self.game_manager.create_session()
        self._ensure_publisher(session)
        session.join(command.username)
        self.publisher.unicast(command.username, RoomCreated(session.room_id, session.color_of(command.username)))

    def _handle_join_room(self, command):
        session = self.game_manager.get_session(command.room_id)
        if session is None:
            self.publisher.unicast(command.username, RoomJoinFailed("room_not_found"))
            return

        # Must be wired before join() - if this fills the second seat,
        # join() fires GAME_STARTED synchronously and NetworkPublisher needs
        # to already be subscribed to push it to the room's creator.
        self._ensure_publisher(session)
        session.join(command.username)
        self.publisher.unicast(
            command.username, RoomJoined(session.room_id, session.color_of(command.username), session.get_state())
        )

    def _handle_move(self, command):
        session = self.game_manager.get_session(command.room_id)
        if session is None:
            return

        source = Position(*command.source)
        destination = Position(*command.destination)

        # Just schedules the move - it may still be mid-flight. MOVE_COMPLETED
        # and GAME_ENDED are only published once time actually advances far
        # enough for it to land, via GameSession.advance() (SessionTicker).
        session.request_move(command.username, source, destination)

        self.publisher.unicast(command.username, GameStateUpdated(session.room_id, session.get_state()))

    def _handle_jump(self, command):
        session = self.game_manager.get_session(command.room_id)
        if session is None:
            return

        position = Position(*command.position)
        session.request_jump(command.username, position)

        self.publisher.unicast(command.username, GameStateUpdated(session.room_id, session.get_state()))

    def _handle_get_state(self, command):
        session = self.game_manager.get_session(command.room_id)
        if session is None:
            return
        self.publisher.unicast(command.username, GameStateUpdated(session.room_id, session.get_state()))

    def _handle_check_reconnect(self, command):
        session = self.game_manager.find_reconnectable_session(command.username)
        if session is None:
            self.publisher.unicast(command.username, NoReconnectAvailable())
            return
        self.publisher.unicast(command.username, ReconnectAvailable(session.room_id, session.color_of(command.username)))
