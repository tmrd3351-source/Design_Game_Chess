RATING_RANGE = 100


class Matchmaker:
    """Pairs players waiting for a game by Elo proximity. find_match() is
    synchronous: if a compatible waiting player already exists it matches
    immediately and returns a ready GameSession with both players seated;
    otherwise the caller is added to the queue and None is returned. The
    real "give up after 1 minute" timeout needs a live server loop to drive
    it and isn't implemented yet - this only ever pairs or waits."""

    def __init__(self, game_manager):
        self.game_manager = game_manager
        self._waiting = []  # list of (username, rating)

    def find_match(self, username, rating):
        for index, (waiting_username, waiting_rating) in enumerate(self._waiting):
            if waiting_username == username:
                continue
            if abs(waiting_rating - rating) <= RATING_RANGE:
                del self._waiting[index]
                session = self.game_manager.create_session()
                session.join(waiting_username)
                session.join(username)
                return session

        if not any(waiting_username == username for waiting_username, _ in self._waiting):
            self._waiting.append((username, rating))
        return None
