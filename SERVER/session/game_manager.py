import uuid

from SERVER.session.game_session import GameSession


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

    def get_session(self, room_id):
        return self.sessions.get(room_id)

    def find_reconnectable_session(self, username):
        """The session `username` is mid-grace-period on, if any - checked
        on login so a player who dropped can be offered their game back."""
        for session in self.sessions.values():
            if session.is_reconnectable(username):
                return session
        return None

    def _generate_room_id(self):
        return uuid.uuid4().hex[:6]
