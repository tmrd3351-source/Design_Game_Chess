import uuid

from session.game_session import GameSession


class GameManager:
    """Registry of live GameSessions, keyed by room_id."""

    def __init__(self, session_factory=None):
        self._session_factory = session_factory or GameSession
        self.sessions = {}

    def create_session(self):
        room_id = self._generate_room_id()
        session = self._session_factory(room_id)
        self.sessions[room_id] = session
        return session

    def join_session(self, room_id):
        return self.sessions.get(room_id)

    def _generate_room_id(self):
        return uuid.uuid4().hex[:6]
