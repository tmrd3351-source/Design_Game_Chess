from SERVER.model.position import Position
from SHARED.network.protocol import (
    LoginCommand, RegisterCommand, PlayCommand, CreateRoomCommand, JoinRoomCommand, MoveCommand, JumpCommand,
    GetStateCommand, CheckReconnectCommand, LoginSucceeded, LoginFailed, RegisterSucceeded, RegisterFailed,
    GameStarted, Waiting, PlayFailed, RoomCreated, RoomJoined, RoomJoinFailed, GameStateUpdated,
    ReconnectAvailable, NoReconnectAvailable,
)


class ConnectionRouter:
    """Dispatches an incoming protocol Command to the right GameSession and
    returns the protocol Response - no transport involved yet. handle() is a
    plain synchronous call today (the "fake transport"); a real WebSocket
    layer later just deserializes bytes into a Command, calls handle(), and
    serializes the Response back out - this class doesn't change either way."""

    def __init__(self, game_manager, auth_service, matchmaker):
        self.game_manager = game_manager
        self.auth_service = auth_service
        self.matchmaker = matchmaker
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
        return handler(command)

    def _handle_login(self, command):
        user = self.auth_service.login(command.username, command.password)
        if user is None:
            return LoginFailed("invalid_credentials")
        return LoginSucceeded(user.username)

    def _handle_register(self, command):
        user = self.auth_service.register(command.username, command.password)
        if user is None:
            return RegisterFailed("username_taken")
        return RegisterSucceeded(user.username)

    def _handle_play(self, command):
        user = self.auth_service.get_user(command.username)
        if user is None:
            return PlayFailed("unknown_user")
        session = self.matchmaker.find_match(command.username, user.rating)
        if session is None:
            return Waiting()
        return GameStarted(session.room_id, session.color_of(command.username))

    def _handle_create_room(self, command):
        session = self.game_manager.create_session()
        session.join(command.username)
        return RoomCreated(session.room_id, session.color_of(command.username))

    def _handle_join_room(self, command):
        session = self.game_manager.join_session(command.room_id)
        if session is None:
            return RoomJoinFailed("room_not_found")
        session.join(command.username)
        return RoomJoined(session.room_id, session.color_of(command.username), session.controller.get_state())

    def _handle_move(self, command):
        session = self.game_manager.join_session(command.room_id)
        if session is None:
            return None
        source = Position(*command.source)
        destination = Position(*command.destination)
        if self._is_legal_attempt(session, command.username, source, destination):
            session.controller.handle_move(source, destination)
        # Just schedules the move - it may still be mid-flight. MOVE_COMPLETED
        # and GAME_ENDED are only published once time actually advances far
        # enough for it to land, via GameSession.advance() (SessionTicker).
        return GameStateUpdated(session.room_id, session.controller.get_state())

    def _handle_jump(self, command):
        session = self.game_manager.join_session(command.room_id)
        if session is None:
            return None
        position = Position(*command.position)
        if self._is_legal_jump_attempt(session, command.username, position):
            session.controller.handle_jump(position)
        return GameStateUpdated(session.room_id, session.controller.get_state())

    def _is_legal_jump_attempt(self, session, username, position):
        board = session.controller.game_engine.board
        if not board.inside_bounds(position):
            return False
        return self._owns_piece_at(session, username, position)

    def _is_legal_attempt(self, session, username, source, destination):
        # Never trust a MoveCommand's coordinates - an out-of-bounds source
        # or destination would otherwise reach Board.get_piece() and crash
        # the connection with an IndexError, since board access assumes
        # valid coordinates rather than checking them itself.
        board = session.controller.game_engine.board
        if not (board.inside_bounds(source) and board.inside_bounds(destination)):
            return False
        return self._owns_piece_at(session, username, source)

    def _owns_piece_at(self, session, username, position):
        """A move is only honored if the piece at `source` belongs to the
        color `username` was seated as - otherwise either player could move
        either side's pieces. Spectators (and empty squares) never own
        anything."""
        piece = session.controller.game_engine.board.get_piece(position)
        if piece is None:
            return False
        return session.color_of(username) == piece.get_color()

    def _handle_get_state(self, command):
        session = self.game_manager.join_session(command.room_id)
        if session is None:
            return None
        return GameStateUpdated(session.room_id, session.controller.get_state())

    def _handle_check_reconnect(self, command):
        session = self.game_manager.find_reconnectable_session(command.username)
        if session is None:
            return NoReconnectAvailable()
        return ReconnectAvailable(session.room_id, session.color_of(command.username))
