import unittest
from unittest.mock import Mock

from events.event_bus import EventBus
from events.event_types import GAME_ENDED
from subscribers.rating_service import RatingService


def make_rating_service(ratings):
    """`ratings` is {username: rating}; find_by_username looks users up from
    it, update_rating records calls onto a plain dict for easy assertions."""
    user_repository = Mock()
    users = {name: Mock(rating=rating) for name, rating in ratings.items()}
    user_repository.find_by_username.side_effect = lambda name: users.get(name)
    events = EventBus()
    RatingService(events, user_repository)
    return events, user_repository


class TestGameEnded(unittest.TestCase):

    def test_equal_ratings_winner_gains_and_loser_loses_the_same_amount(self):
        events, user_repository = make_rating_service({"alice": 1200, "bob": 1200})

        events.publish(GAME_ENDED, room_id="room-1", winner="w",
                       players={"w": "alice", "b": "bob"})

        user_repository.update_rating.assert_any_call("alice", 1216)
        user_repository.update_rating.assert_any_call("bob", 1184)

    def test_higher_rated_winner_gains_less_than_an_even_match(self):
        events, user_repository = make_rating_service({"alice": 1400, "bob": 1200})

        events.publish(GAME_ENDED, room_id="room-1", winner="w",
                       players={"w": "alice", "b": "bob"})

        winner_call = next(c for c in user_repository.update_rating.call_args_list if c.args[0] == "alice")
        gained = winner_call.args[1] - 1400
        self.assertLess(gained, 16)
        self.assertGreater(gained, 0)

    def test_black_can_be_the_winner(self):
        events, user_repository = make_rating_service({"alice": 1200, "bob": 1200})

        events.publish(GAME_ENDED, room_id="room-1", winner="b",
                       players={"w": "alice", "b": "bob"})

        user_repository.update_rating.assert_any_call("bob", 1216)
        user_repository.update_rating.assert_any_call("alice", 1184)

    def test_updates_both_players_exactly_once(self):
        events, user_repository = make_rating_service({"alice": 1200, "bob": 1200})

        events.publish(GAME_ENDED, room_id="room-1", winner="w",
                       players={"w": "alice", "b": "bob"})

        self.assertEqual(user_repository.update_rating.call_count, 2)

    def test_missing_player_in_the_mapping_is_a_no_op(self):
        events, user_repository = make_rating_service({"alice": 1200})

        events.publish(GAME_ENDED, room_id="room-1", winner="w", players={"w": "alice"})

        user_repository.update_rating.assert_not_called()

    def test_ignores_events_it_did_not_subscribe_to(self):
        events, user_repository = make_rating_service({"alice": 1200, "bob": 1200})

        events.publish("some_other_event", foo="bar")

        user_repository.update_rating.assert_not_called()


if __name__ == "__main__":
    unittest.main()
