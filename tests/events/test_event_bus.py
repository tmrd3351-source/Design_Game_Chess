import unittest
from unittest.mock import Mock

from events.event_bus import EventBus


class TestSubscribeAndPublish(unittest.TestCase):

    def test_publish_calls_a_subscribed_callback(self):
        bus = EventBus()
        callback = Mock()
        bus.subscribe("move_made", callback)

        bus.publish("move_made", piece="R")

        callback.assert_called_once_with(piece="R")

    def test_publish_calls_every_subscriber_for_that_event(self):
        bus = EventBus()
        first, second = Mock(), Mock()
        bus.subscribe("move_made", first)
        bus.subscribe("move_made", second)

        bus.publish("move_made")

        first.assert_called_once()
        second.assert_called_once()

    def test_subscribers_are_called_in_subscription_order(self):
        bus = EventBus()
        order = []
        bus.subscribe("move_made", lambda: order.append("first"))
        bus.subscribe("move_made", lambda: order.append("second"))

        bus.publish("move_made")

        self.assertEqual(order, ["first", "second"])

    def test_publish_with_no_subscribers_does_nothing(self):
        bus = EventBus()
        bus.publish("move_made")  # must not raise

    def test_subscribers_to_a_different_event_are_not_called(self):
        bus = EventBus()
        callback = Mock()
        bus.subscribe("move_made", callback)

        bus.publish("game_over")

        callback.assert_not_called()

    def test_same_callback_can_subscribe_to_multiple_events(self):
        bus = EventBus()
        callback = Mock()
        bus.subscribe("move_made", callback)
        bus.subscribe("game_over", callback)

        bus.publish("move_made")
        bus.publish("game_over")

        self.assertEqual(callback.call_count, 2)

    def test_publish_forwards_keyword_arguments_to_the_callback(self):
        bus = EventBus()
        callback = Mock()
        bus.subscribe("game_over", callback)

        bus.publish("game_over", winner="w", reason="checkmate")

        callback.assert_called_once_with(winner="w", reason="checkmate")

    def test_two_independent_buses_do_not_share_subscribers(self):
        bus_a, bus_b = EventBus(), EventBus()
        callback = Mock()
        bus_a.subscribe("move_made", callback)

        bus_b.publish("move_made")

        callback.assert_not_called()


if __name__ == "__main__":
    unittest.main()
