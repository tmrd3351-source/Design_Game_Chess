from events.event_types import GAME_ENDED

K_FACTOR = 32


def _expected_score(rating, opponent_rating):
    return 1 / (1 + 10 ** ((opponent_rating - rating) / 400))


def _updated_rating(rating, opponent_rating, score):
    return round(rating + K_FACTOR * (score - _expected_score(rating, opponent_rating)))


class RatingService:
    """Subscribes to GAME_ENDED and updates both players' Elo via
    UserRepository directly - never through AuthService, since
    login/registration and rating are separate concerns."""

    def __init__(self, events, user_repository):
        events.subscribe(GAME_ENDED, self._on_game_ended)
        self.user_repository = user_repository

    def _on_game_ended(self, room_id, winner, players):
        loser_color = "b" if winner == "w" else "w"
        winner_username = players.get(winner)
        loser_username = players.get(loser_color)
        if winner_username is None or loser_username is None:
            return

        winner_user = self.user_repository.find_by_username(winner_username)
        loser_user = self.user_repository.find_by_username(loser_username)

        new_winner_rating = _updated_rating(winner_user.rating, loser_user.rating, 1)
        new_loser_rating = _updated_rating(loser_user.rating, winner_user.rating, 0)

        self.user_repository.update_rating(winner_username, new_winner_rating)
        self.user_repository.update_rating(loser_username, new_loser_rating)
