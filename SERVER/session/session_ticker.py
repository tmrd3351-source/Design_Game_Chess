import time


class SessionTicker:
    """Drives real elapsed time into every active GameSession - the
    server-side sibling of GameWindow's frame loop. Depends only on
    GameManager/GameSession - never touches Controller or engine internals
    directly, since GameSession.advance() already owns all of that."""

    def __init__(self, game_manager):
        self.game_manager = game_manager
        self._last_tick = time.time()

    def tick(self, now=None):
        now = time.time() if now is None else now
        elapsed_ms = int((now - self._last_tick) * 1000)
        self._last_tick = now
        if elapsed_ms <= 0:
            return

        for session in list(self.game_manager.sessions.values()):
            session.advance(elapsed_ms)
