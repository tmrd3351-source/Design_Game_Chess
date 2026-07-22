import unittest
from unittest.mock import Mock

from CLIENT.gui.home_screen import HomeScreen, ENTER_KEY, BACKSPACE_KEY
from SHARED.network.protocol import (
    PlayCommand, CreateRoomCommand, JoinRoomCommand, CheckReconnectCommand,
    Waiting, GameStarted, PlayFailed, RoomCreated, RoomJoined, RoomJoinFailed,
    ReconnectAvailable, NoReconnectAvailable,
)


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


class TestCreateRoom(unittest.TestCase):

    def test_sends_a_create_room_command_with_the_username(self):
        network = Mock()
        screen = make_screen(network)

        screen.create_room()

        network.send.assert_called_once()
        sent = network.send.call_args.args[0]
        self.assertIsInstance(sent, CreateRoomCommand)
        self.assertEqual(sent.username, "alice")

    def test_sets_status_to_waiting(self):
        screen = make_screen()
        screen.create_room()
        self.assertEqual(screen.status, "waiting")


class TestJoinRoom(unittest.TestCase):

    def test_sends_a_join_room_command_with_username_and_room_id(self):
        network = Mock()
        screen = make_screen(network)

        screen.join_room("3bb777")

        network.send.assert_called_once()
        sent = network.send.call_args.args[0]
        self.assertIsInstance(sent, JoinRoomCommand)
        self.assertEqual(sent.username, "alice")
        self.assertEqual(sent.room_id, "3bb777")

    def test_sets_status_to_waiting(self):
        screen = make_screen()
        screen.join_room("3bb777")
        self.assertEqual(screen.status, "waiting")


class TestCheckReconnect(unittest.TestCase):

    def test_sends_a_check_reconnect_command_with_the_username(self):
        network = Mock()
        screen = make_screen(network)

        screen.check_reconnect()

        network.send.assert_called_once()
        sent = network.send.call_args.args[0]
        self.assertIsInstance(sent, CheckReconnectCommand)
        self.assertEqual(sent.username, "alice")


class TestReconnectPrompt(unittest.TestCase):

    def test_reconnect_available_response_shows_the_prompt(self):
        network = Mock()
        network.poll.return_value = ReconnectAvailable("3bb777", "w")
        screen = make_screen(network)

        screen.poll_network()

        self.assertEqual(screen.status, "reconnect_prompt")
        self.assertEqual(screen.room_id, "3bb777")
        self.assertEqual(screen.color, "w")
        self.assertIn("3bb777", screen.message)

    def test_no_reconnect_available_leaves_the_screen_idle(self):
        network = Mock()
        network.poll.return_value = NoReconnectAvailable()
        screen = make_screen(network)

        screen.poll_network()

        self.assertEqual(screen.status, "idle")

    def test_pressing_y_sends_a_join_room_command_for_the_offered_room(self):
        network = Mock()
        network.poll.return_value = ReconnectAvailable("3bb777", "w")
        screen = make_screen(network)
        screen.poll_network()

        screen.handle_key(ord("y"))

        network.send.assert_called_once()
        sent = network.send.call_args.args[0]
        self.assertIsInstance(sent, JoinRoomCommand)
        self.assertEqual(sent.username, "alice")
        self.assertEqual(sent.room_id, "3bb777")
        self.assertEqual(screen.status, "waiting")

    def test_y_is_case_insensitive(self):
        network = Mock()
        network.poll.return_value = ReconnectAvailable("3bb777", "w")
        screen = make_screen(network)
        screen.poll_network()

        screen.handle_key(ord("Y"))

        network.send.assert_called_once()

    def test_pressing_n_declines_and_returns_to_idle_without_sending_anything(self):
        network = Mock()
        network.poll.return_value = ReconnectAvailable("3bb777", "w")
        screen = make_screen(network)
        screen.poll_network()

        screen.handle_key(ord("n"))

        network.send.assert_not_called()
        self.assertEqual(screen.status, "idle")

    def test_other_keys_do_nothing_while_the_prompt_is_showing(self):
        network = Mock()
        network.poll.return_value = ReconnectAvailable("3bb777", "w")
        screen = make_screen(network)
        screen.poll_network()

        screen.handle_key(ord("p"))

        network.send.assert_not_called()
        self.assertEqual(screen.status, "reconnect_prompt")


class TestRoomIdEntry(unittest.TestCase):

    def test_typing_letters_and_digits_appends_to_the_buffer(self):
        network = Mock()
        screen = make_screen(network)
        screen.handle_key(ord("j"))

        screen.handle_key(ord("3"))
        screen.handle_key(ord("b"))
        screen.handle_key(ord("B"))

        self.assertEqual(screen.room_id_input, "3bb")
        network.send.assert_not_called()

    def test_backspace_removes_the_last_character(self):
        network = Mock()
        screen = make_screen(network)
        screen.handle_key(ord("j"))
        screen.handle_key(ord("a"))
        screen.handle_key(ord("b"))

        screen.handle_key(BACKSPACE_KEY)

        self.assertEqual(screen.room_id_input, "a")

    def test_backspace_on_empty_buffer_does_nothing(self):
        network = Mock()
        screen = make_screen(network)
        screen.handle_key(ord("j"))

        screen.handle_key(BACKSPACE_KEY)

        self.assertEqual(screen.room_id_input, "")

    def test_enter_sends_join_room_command_with_the_typed_id(self):
        network = Mock()
        screen = make_screen(network)
        screen.handle_key(ord("j"))
        for char in "3bb777":
            screen.handle_key(ord(char))

        screen.handle_key(ENTER_KEY)

        network.send.assert_called_once()
        sent = network.send.call_args.args[0]
        self.assertIsInstance(sent, JoinRoomCommand)
        self.assertEqual(sent.room_id, "3bb777")
        self.assertEqual(screen.status, "waiting")

    def test_enter_on_an_empty_buffer_sends_nothing(self):
        network = Mock()
        screen = make_screen(network)
        screen.handle_key(ord("j"))

        screen.handle_key(ENTER_KEY)

        network.send.assert_not_called()
        self.assertEqual(screen.status, "entering_room_id")

    def test_other_keys_while_entering_a_room_id_do_not_trigger_play_or_create(self):
        network = Mock()
        screen = make_screen(network)
        screen.handle_key(ord("j"))

        screen.handle_key(ord("p"))  # typed as a room-id character, not the Play shortcut
        screen.handle_key(ord("c"))

        network.send.assert_not_called()
        self.assertEqual(screen.room_id_input, "pc")


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

    def test_c_triggers_create_room(self):
        network = Mock()
        screen = make_screen(network)

        screen.handle_key(ord("c"))

        network.send.assert_called_once()
        sent = network.send.call_args.args[0]
        self.assertIsInstance(sent, CreateRoomCommand)
        self.assertEqual(screen.status, "waiting")

    def test_j_enters_room_id_input_mode_without_sending_anything(self):
        network = Mock()
        screen = make_screen(network)

        screen.handle_key(ord("j"))

        network.send.assert_not_called()
        self.assertEqual(screen.status, "entering_room_id")
        self.assertEqual(screen.room_id_input, "")

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

    def test_game_started_response_stores_the_players_own_color(self):
        network = Mock()
        network.poll.return_value = GameStarted("room-1", "b")
        screen = make_screen(network)

        screen.poll_network()

        self.assertEqual(screen.color, "b")

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

    def test_play_failed_response_resets_status_to_idle_with_a_message(self):
        network = Mock()
        network.poll.return_value = PlayFailed("unknown_user")
        screen = make_screen(network)
        screen.status = "waiting"  # was waiting before the server replied

        screen.poll_network()

        self.assertEqual(screen.status, "idle")
        self.assertIn("unknown_user", screen.message)

    def test_room_created_response_sets_waiting_status_room_id_and_color(self):
        network = Mock()
        network.poll.return_value = RoomCreated("3bb777", "w")
        screen = make_screen(network)

        screen.poll_network()

        self.assertEqual(screen.status, "waiting")
        self.assertEqual(screen.room_id, "3bb777")
        self.assertEqual(screen.color, "w")
        self.assertIn("3bb777", screen.message)

    def test_room_joined_response_sets_started_status_room_id_and_color(self):
        network = Mock()
        network.poll.return_value = RoomJoined("3bb777", "b", state=Mock())
        screen = make_screen(network)

        screen.poll_network()

        self.assertEqual(screen.status, "started")
        self.assertEqual(screen.room_id, "3bb777")
        self.assertEqual(screen.color, "b")

    def test_room_joined_pushed_to_the_creator_also_starts_the_game(self):
        # Same response type/handling whether it's the joiner's own direct
        # reply or the creator's unsolicited push once someone else joins.
        network = Mock()
        screen = make_screen(network)
        network.poll.return_value = RoomJoined("3bb777", "w", state=Mock())

        screen.poll_network()

        self.assertTrue(screen.handle_key(ord("z")))

    def test_room_join_failed_response_resets_status_to_idle_with_a_message(self):
        network = Mock()
        network.poll.return_value = RoomJoinFailed("room_not_found")
        screen = make_screen(network)
        screen.status = "waiting"

        screen.poll_network()

        self.assertEqual(screen.status, "idle")
        self.assertIn("room_not_found", screen.message)


if __name__ == "__main__":
    unittest.main()
