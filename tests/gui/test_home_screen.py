import unittest
from unittest.mock import Mock

from gui.home_screen import HomeScreen
from network.protocol import PlayCommand, Waiting, GameStarted


def make_screen(network=None):
    return HomeScreen("alice", network=network or Mock())


class TestConstruction(unittest.TestCase):

    def test_starts_idle_with_no_room(self):
        screen = make_screen()
        self.assertEqual(screen.status, "idle")
        self.assertEqual(screen.message, "")
        self.assertIsNone(screen.room_id)

    def test_stores_the_username(self):
        screen = make_screen()
        self.assertEqual(screen.username, "alice")


class TestPlay(unittest.TestCase):

    def test_sends_a_play_command_with_the_username(self):
        network = Mock()
        screen = make_screen(network)

        screen.play()

        network.send.assert_called_once()
        sent = network.send.call_args.args[0]
        self.assertIsInstance(sent, PlayCommand)
        self.assertEqual(sent.username, "alice")

    def test_sets_status_to_waiting(self):
        screen = make_screen()
        screen.play()
        self.assertEqual(screen.status, "waiting")
        self.assertIn("Waiting", screen.message)


class TestHandleKey(unittest.TestCase):

    def test_p_triggers_play(self):
        network = Mock()
        screen = make_screen(network)

        screen.handle_key(ord("p"))

        network.send.assert_called_once()
        self.assertEqual(screen.status, "waiting")

    def test_p_is_case_insensitive(self):
        network = Mock()
        screen = make_screen(network)

        screen.handle_key(ord("P"))

        network.send.assert_called_once()

    def test_c_sets_a_not_wired_up_message_without_changing_status(self):
        screen = make_screen()
        screen.handle_key(ord("c"))
        self.assertIn("Create Room", screen.message)
        self.assertEqual(screen.status, "idle")

    def test_j_sets_a_not_wired_up_message_without_changing_status(self):
        screen = make_screen()
        screen.handle_key(ord("j"))
        self.assertIn("Join Room", screen.message)
        self.assertEqual(screen.status, "idle")

    def test_returns_false_while_status_is_not_started(self):
        screen = make_screen()
        self.assertFalse(screen.handle_key(ord("p")))

    def test_unrecognized_key_does_nothing(self):
        screen = make_screen()
        self.assertFalse(screen.handle_key(ord("z")))
        self.assertEqual(screen.status, "idle")
        self.assertEqual(screen.message, "")


class TestPollNetwork(unittest.TestCase):

    def test_no_pending_message_leaves_state_unchanged(self):
        network = Mock()
        network.poll.return_value = None
        screen = make_screen(network)

        screen.poll_network()

        self.assertEqual(screen.status, "idle")

    def test_waiting_response_sets_status_and_message(self):
        network = Mock()
        network.poll.return_value = Waiting()
        screen = make_screen(network)

        screen.poll_network()

        self.assertEqual(screen.status, "waiting")
        self.assertIn("Waiting", screen.message)

    def test_game_started_response_sets_status_room_id_and_message(self):
        network = Mock()
        network.poll.return_value = GameStarted("room-1")
        screen = make_screen(network)

        screen.poll_network()

        self.assertEqual(screen.status, "started")
        self.assertEqual(screen.room_id, "room-1")
        self.assertIn("room-1", screen.message)

    def test_game_started_via_poll_is_reflected_in_handle_key_return_value(self):
        # Simulates the first (already-waiting) player: they never call
        # play() again themselves - the match arrives as an unsolicited
        # push picked up by poll_network(), and the *next* keypress should
        # report the game has started.
        network = Mock()
        screen = make_screen(network)
        network.poll.return_value = GameStarted("room-1")

        screen.poll_network()

        self.assertTrue(screen.handle_key(ord("z")))
        self.assertEqual(screen.room_id, "room-1")


if __name__ == "__main__":
    unittest.main()
