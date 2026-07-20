from model.position import Position
from network.protocol import (
    LoginCommand, PlayCommand, CreateRoomCommand, JoinRoomCommand, MoveCommand,
    LoginSucceeded, LoginFailed, GameStarted, Waiting, RoomCreated, GameStateUpdated,
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
            PlayCommand: self._handle_play,
            CreateRoomCommand: self._handle_create_room,
            JoinRoomCommand: self._handle_join_room,
            MoveCommand: self._handle_move,
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

    def _handle_play(self, command):
        user = self.auth_service.get_user(command.username)
        if user is None:
            return None
        session = self.matchmaker.find_match(command.username, user.rating)
        if session is None:
            return Waiting()
        return GameStarted(session.room_id)

    def _handle_create_room(self, command):
        session = self.game_manager.create_session()
        session.join(command.username)
        return RoomCreated(session.room_id)

    def _handle_join_room(self, command):
        session = self.game_manager.join_session(command.room_id)
        if session is None:
            return None
        session.join(command.username)
        return GameStateUpdated(session.room_id, session.controller.get_state())

    def _handle_move(self, command):
        session = self.game_manager.join_session(command.room_id)
        if session is None:
            return None
        source = Position(*command.source)
        destination = Position(*command.destination)
        session.controller.handle_move(source, destination)
        # Just schedules the move - it may still be mid-flight. MOVE_COMPLETED
        # and GAME_ENDED are only published once time actually advances far
        # enough for it to land, via GameSession.advance() (SessionTicker).
        return GameStateUpdated(session.room_id, session.controller.get_state())
