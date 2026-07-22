import unittest
from unittest.mock import Mock

from SERVER.events.event_bus import EventBus
from SERVER.events.event_types import PLAYER_JOINED, GAME_STARTED
from SERVER.subscribers.session_logger import SessionLogger
from SERVER.session.game_session import GameSession


class TestSessionLogger(unittest.TestCase):

    def test_starts_with_no_lines(self):
        logger = SessionLogger(EventBus())
        self.assertEqual(logger.lines, [])

    def test_logs_a_player_joined_event(self):
        events = EventBus()
        logger = SessionLogger(events)

        events.publish(PLAYER_JOINED, name="alice", role="w")

        self.assertEqual(logger.lines, ["alice joined as w"])

    def test_logs_a_game_started_event(self):
        events = EventBus()
        logger = SessionLogger(events)

        events.publish(GAME_STARTED, room_id="room-42")

        self.assertEqual(logger.lines, ["game started in room room-42"])

    def test_logs_multiple_events_in_publish_order(self):
        events = EventBus()
        logger = SessionLogger(events)

        events.publish(PLAYER_JOINED, name="alice", role="w")
        events.publish(PLAYER_JOINED, name="bob", role="b")
        events.publish(GAME_STARTED, room_id="room-42")

        self.assertEqual(logger.lines, [
            "alice joined as w",
            "bob joined as b",
            "game started in room room-42",
        ])

    def test_ignores_events_it_did_not_subscribe_to(self):
        events = EventBus()
        logger = SessionLogger(events)

        events.publish("some_other_event", foo="bar")

        self.assertEqual(logger.lines, [])

    def test_wired_end_to_end_through_a_real_game_session(self):
        session = GameSession("room-1", controller_factory=lambda: Mock())
        logger = SessionLogger(session.events)

        session.join("alice")
        session.join("bob")

        self.assertEqual(logger.lines, [
            "alice joined as w",
            "bob joined as b",
            "game started in room room-1",
        ])


if __name__ == "__main__":
    unittest.main()
