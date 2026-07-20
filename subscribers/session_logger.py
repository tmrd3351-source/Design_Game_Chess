from events.event_types import PLAYER_JOINED, GAME_STARTED


class SessionLogger:
    """Proves the GameSession -> EventBus -> subscriber chain end to end by
    recording PLAYER_JOINED and GAME_STARTED as they're published. Keeps its
    lines in memory rather than writing to disk - a real log sink can replace
    this later without touching how it's wired up."""

    def __init__(self, events):
        events.subscribe(PLAYER_JOINED, self._on_player_joined)
        events.subscribe(GAME_STARTED, self._on_game_started)
        self.lines = []

    def _on_player_joined(self, name, role):
        self.lines.append(f"{name} joined as {role}")

    def _on_game_started(self, room_id):
        self.lines.append(f"game started in room {room_id}")
