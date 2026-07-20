import unittest
from unittest.mock import patch

from events.event_bus import EventBus
from events.event_types import MOVE_COMPLETED
from network.network_publisher import NetworkPublisher
from network.protocol import GameStateUpdated


class TestNetworkPublisher(unittest.TestCase):

    def test_move_completed_produces_a_game_state_updated_response(self):
        events = EventBus()
        sent = []
        NetworkPublisher(events, sink=sent.append)

        events.publish(MOVE_COMPLETED, room_id="room-1", state="the_state")

        self.assertEqual(len(sent), 1)
        self.assertIsInstance(sent[0], GameStateUpdated)
        self.assertEqual(sent[0].room_id, "room-1")
        self.assertEqual(sent[0].state, "the_state")

    def test_ignores_events_it_did_not_subscribe_to(self):
        events = EventBus()
        sent = []
        NetworkPublisher(events, sink=sent.append)

        events.publish("some_other_event", foo="bar")

        self.assertEqual(sent, [])

    @patch("builtins.print")
    def test_defaults_to_print_when_no_sink_given(self, mock_print):
        events = EventBus()
        NetworkPublisher(events)

        events.publish(MOVE_COMPLETED, room_id="room-1", state="the_state")

        mock_print.assert_called_once()
        self.assertIsInstance(mock_print.call_args.args[0], GameStateUpdated)

    def test_multiple_move_completed_events_each_produce_their_own_response(self):
        events = EventBus()
        sent = []
        NetworkPublisher(events, sink=sent.append)

        events.publish(MOVE_COMPLETED, room_id="room-1", state="state_a")
        events.publish(MOVE_COMPLETED, room_id="room-1", state="state_b")

        self.assertEqual([response.state for response in sent], ["state_a", "state_b"])


if __name__ == "__main__":
    unittest.main()
