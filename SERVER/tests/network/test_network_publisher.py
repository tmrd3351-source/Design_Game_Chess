import unittest
from unittest.mock import Mock, patch

from SERVER.events.event_bus import EventBus
from SERVER.events.event_types import MOVE_COMPLETED, GAME_STARTED, GAME_ENDED
from SERVER.network.network_publisher import NetworkPublisher
from SHARED.network.protocol import GameStateUpdated, GameStarted


def make_session():
    session = Mock()
    session.events = EventBus()
    return session


class TestMoveCompleted(unittest.TestCase):

    def test_move_completed_produces_a_game_state_updated_response(self):
        session = make_session()
        sent = []
        NetworkPublisher(session, broadcast=sent.append)

        session.events.publish(MOVE_COMPLETED, room_id="room-1", state="the_state")

        self.assertEqual(len(sent), 1)
        self.assertIsInstance(sent[0], GameStateUpdated)
        self.assertEqual(sent[0].room_id, "room-1")
        self.assertEqual(sent[0].state, "the_state")

    def test_ignores_events_it_did_not_subscribe_to(self):
        session = make_session()
        sent = []
        NetworkPublisher(session, broadcast=sent.append)

        session.events.publish("some_other_event", foo="bar")

        self.assertEqual(sent, [])

    @patch("builtins.print")
    def test_defaults_to_print_when_no_broadcast_given(self, mock_print):
        session = make_session()
        NetworkPublisher(session)

        session.events.publish(MOVE_COMPLETED, room_id="room-1", state="the_state")

        mock_print.assert_called_once()
        self.assertIsInstance(mock_print.call_args.args[0], GameStateUpdated)

    def test_multiple_move_completed_events_each_produce_their_own_response(self):
        session = make_session()
        sent = []
        NetworkPublisher(session, broadcast=sent.append)

        session.events.publish(MOVE_COMPLETED, room_id="room-1", state="state_a")
        session.events.publish(MOVE_COMPLETED, room_id="room-1", state="state_b")

        self.assertEqual([response.state for response in sent], ["state_a", "state_b"])


def make_seated_session(players=None):
    session = make_session()
    session.players = players or {"w": "alice", "b": "bob"}
    session.color_of.side_effect = lambda name: next(
        (color for color, username in session.players.items() if username == name), None
    )
    return session


class TestGameStarted(unittest.TestCase):

    def test_sends_each_seated_player_their_own_color_via_unicast(self):
        session = make_seated_session()
        sent = []
        NetworkPublisher(session, unicast=lambda username, response: sent.append((username, response)))

        session.events.publish(GAME_STARTED, room_id="room-1")

        self.assertEqual(len(sent), 2)
        recipients = dict(sent)
        self.assertIsInstance(recipients["alice"], GameStarted)
        self.assertEqual(recipients["alice"].room_id, "room-1")
        self.assertEqual(recipients["alice"].color, "w")
        self.assertIsInstance(recipients["bob"], GameStarted)
        self.assertEqual(recipients["bob"].color, "b")

    def test_never_goes_through_broadcast(self):
        # GameStarted is per-recipient (each player needs their own color),
        # so it always goes through unicast, never the room-wide broadcast.
        session = make_seated_session()
        broadcast_sent = []
        NetworkPublisher(session, broadcast=broadcast_sent.append, unicast=lambda *_: None)

        session.events.publish(GAME_STARTED, room_id="room-1")

        self.assertEqual(broadcast_sent, [])

    @patch("builtins.print")
    def test_defaults_to_print_when_no_unicast_given(self, mock_print):
        session = make_seated_session(players={"w": "alice"})
        NetworkPublisher(session)

        session.events.publish(GAME_STARTED, room_id="room-1")

        mock_print.assert_called_once_with("alice", mock_print.call_args.args[1])


class TestGameEnded(unittest.TestCase):

    def test_broadcasts_a_game_state_updated_with_the_sessions_current_state(self):
        session = make_session()
        session.get_state.return_value = "the_final_state"
        sent = []
        NetworkPublisher(session, broadcast=sent.append)

        session.events.publish(GAME_ENDED, room_id="room-1", winner="w", players={"w": "alice", "b": "bob"})

        self.assertEqual(len(sent), 1)
        self.assertIsInstance(sent[0], GameStateUpdated)
        self.assertEqual(sent[0].room_id, "room-1")
        self.assertEqual(sent[0].state, "the_final_state")


if __name__ == "__main__":
    unittest.main()
