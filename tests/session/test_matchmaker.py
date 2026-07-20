import unittest
from unittest.mock import Mock

from session.matchmaker import Matchmaker


def make_matchmaker():
    game_manager = Mock()
    return Matchmaker(game_manager), game_manager


class TestFindMatch(unittest.TestCase):

    def test_first_seeker_gets_no_match_and_is_queued(self):
        matchmaker, game_manager = make_matchmaker()

        result = matchmaker.find_match("alice", 1200)

        self.assertIsNone(result)
        game_manager.create_session.assert_not_called()

    def test_second_seeker_within_range_is_matched_immediately(self):
        matchmaker, game_manager = make_matchmaker()
        session = Mock()
        game_manager.create_session.return_value = session
        matchmaker.find_match("alice", 1200)

        result = matchmaker.find_match("bob", 1250)

        self.assertIs(result, session)

    def test_matching_creates_exactly_one_new_session(self):
        matchmaker, game_manager = make_matchmaker()
        game_manager.create_session.return_value = Mock()
        matchmaker.find_match("alice", 1200)

        matchmaker.find_match("bob", 1250)

        game_manager.create_session.assert_called_once()

    def test_matching_seats_both_the_waiting_and_the_new_seeker(self):
        matchmaker, game_manager = make_matchmaker()
        session = Mock()
        game_manager.create_session.return_value = session
        matchmaker.find_match("alice", 1200)

        matchmaker.find_match("bob", 1250)

        session.join.assert_any_call("alice")
        session.join.assert_any_call("bob")
        self.assertEqual(session.join.call_count, 2)

    def test_seeker_outside_the_rating_range_is_not_matched(self):
        matchmaker, game_manager = make_matchmaker()
        matchmaker.find_match("alice", 1200)

        result = matchmaker.find_match("bob", 1301)  # +101, just outside range

        self.assertIsNone(result)
        game_manager.create_session.assert_not_called()

    def test_seeker_exactly_at_the_edge_of_the_range_is_matched(self):
        matchmaker, game_manager = make_matchmaker()
        game_manager.create_session.return_value = Mock()
        matchmaker.find_match("alice", 1200)

        result = matchmaker.find_match("bob", 1300)  # +100, exactly at the edge

        self.assertIsNotNone(result)

    def test_a_matched_player_is_removed_from_the_waiting_queue(self):
        matchmaker, game_manager = make_matchmaker()
        game_manager.create_session.side_effect = lambda: Mock()
        matchmaker.find_match("alice", 1200)
        matchmaker.find_match("bob", 1250)  # matches and removes alice

        # bob is gone too (matched), so a third seeker should wait, not
        # re-match with either of them
        result = matchmaker.find_match("carol", 1220)

        self.assertIsNone(result)

    def test_three_waiting_players_match_the_first_compatible_one(self):
        matchmaker, game_manager = make_matchmaker()
        game_manager.create_session.return_value = Mock()
        matchmaker.find_match("alice", 1000)
        matchmaker.find_match("bob", 1200)

        result = matchmaker.find_match("carol", 1210)  # compatible with bob only

        self.assertIsNotNone(result)

    def test_a_username_never_matches_its_own_earlier_queue_entry(self):
        # Regression: calling find_match twice for the same username (e.g. a
        # stale queued request from an earlier attempt) must not self-match.
        matchmaker, game_manager = make_matchmaker()
        matchmaker.find_match("alice", 1200)

        result = matchmaker.find_match("alice", 1200)

        self.assertIsNone(result)
        game_manager.create_session.assert_not_called()

    def test_a_username_already_waiting_is_not_enqueued_twice(self):
        matchmaker, _ = make_matchmaker()
        matchmaker.find_match("alice", 1200)
        matchmaker.find_match("alice", 1200)

        self.assertEqual(matchmaker._waiting, [("alice", 1200)])

    def test_a_third_seeker_still_matches_the_genuinely_waiting_username(self):
        matchmaker, game_manager = make_matchmaker()
        session = Mock()
        game_manager.create_session.return_value = session
        matchmaker.find_match("alice", 1200)
        matchmaker.find_match("alice", 1200)  # repeated/stale request, ignored

        result = matchmaker.find_match("bob", 1200)

        self.assertIs(result, session)
        session.join.assert_any_call("alice")
        session.join.assert_any_call("bob")


if __name__ == "__main__":
    unittest.main()
