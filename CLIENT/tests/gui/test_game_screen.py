import unittest
from unittest.mock import Mock

from CLIENT.gui.game_screen import GameScreen
from SHARED.network.protocol import MoveCommand, JumpCommand, GameStateUpdated, Waiting
from CLIENT.network.remote_state import RemoteGameState
from CLIENT.model.position import Position


def make_screen(network=None, my_color=None):
    return GameScreen("alice", "room-1", my_color, network=network or Mock())


def make_state_dict():
    return {
        "board": {"rows": 8, "cols": 8, "pieces": []},
        "winner": None,
        "game_over": False,
        "motions": [],
    }


class TestConstruction(unittest.TestCase):

    def test_starts_with_no_state_and_nothing_selected(self):
        screen = make_screen()
        self.assertIsNone(screen.state)
        self.assertIsNone(screen.selected)

    def test_stores_username_and_room_id(self):
        screen = make_screen()
        self.assertEqual(screen.username, "alice")
        self.assertEqual(screen.room_id, "room-1")

    def test_stores_the_players_own_color(self):
        screen = make_screen(my_color="w")
        self.assertEqual(screen.my_color, "w")


class TestPollNetwork(unittest.TestCase):

    def test_no_pending_message_leaves_state_unchanged(self):
        network = Mock()
        network.poll.return_value = None
        screen = make_screen(network)

        screen.poll_network()

        self.assertIsNone(screen.state)

    def test_matching_room_id_updates_state(self):
        network = Mock()
        network.poll.return_value = GameStateUpdated("room-1", make_state_dict())
        screen = make_screen(network)

        screen.poll_network()

        self.assertIsInstance(screen.state, RemoteGameState)
        self.assertEqual(screen.state.board.rows, 8)

    def test_a_different_rooms_update_is_ignored(self):
        network = Mock()
        network.poll.return_value = GameStateUpdated("some-other-room", make_state_dict())
        screen = make_screen(network)

        screen.poll_network()

        self.assertIsNone(screen.state)

    def test_a_non_state_response_is_ignored(self):
        network = Mock()
        network.poll.return_value = Waiting()
        screen = make_screen(network)

        screen.poll_network()

        self.assertIsNone(screen.state)

    def test_a_later_update_replaces_the_earlier_state(self):
        network = Mock()
        screen = make_screen(network)
        network.poll.return_value = GameStateUpdated("room-1", make_state_dict())
        screen.poll_network()
        first_state = screen.state

        second_dict = make_state_dict()
        second_dict["game_over"] = True
        network.poll.return_value = GameStateUpdated("room-1", second_dict)
        screen.poll_network()

        self.assertIsNot(screen.state, first_state)
        self.assertTrue(screen.state.game_over)


class TestHandleClick(unittest.TestCase):

    def test_first_click_selects_without_sending_anything(self):
        network = Mock()
        screen = make_screen(network)

        screen.handle_click(Position(6, 0))

        self.assertTrue(screen.selected.equals(Position(6, 0)))
        network.send.assert_not_called()

    def test_second_click_sends_a_move_command_and_clears_selection(self):
        network = Mock()
        screen = make_screen(network)
        screen.handle_click(Position(6, 0))

        screen.handle_click(Position(5, 0))

        self.assertIsNone(screen.selected)
        network.send.assert_called_once()
        sent = network.send.call_args.args[0]
        self.assertIsInstance(sent, MoveCommand)
        self.assertEqual(sent.username, "alice")
        self.assertEqual(sent.room_id, "room-1")
        self.assertEqual(sent.source, (6, 0))
        self.assertEqual(sent.destination, (5, 0))

    def test_a_third_click_starts_a_new_selection(self):
        network = Mock()
        screen = make_screen(network)
        screen.handle_click(Position(6, 0))
        screen.handle_click(Position(5, 0))  # sends the move, clears selection

        screen.handle_click(Position(1, 4))

        self.assertTrue(screen.selected.equals(Position(1, 4)))
        self.assertEqual(network.send.call_count, 1)

    def test_a_click_past_the_boards_right_edge_is_ignored(self):
        # The window is wider than the board (there's a score panel to the
        # right of it) - a click out there must never become a selection or
        # reach a MoveCommand, since it isn't a real board square at all.
        network = Mock()
        screen = make_screen(network)

        screen.handle_click(Position(0, 8))

        self.assertIsNone(screen.selected)
        network.send.assert_not_called()

    def test_a_click_with_a_negative_row_is_ignored(self):
        network = Mock()
        screen = make_screen(network)

        screen.handle_click(Position(-1, 0))

        self.assertIsNone(screen.selected)
        network.send.assert_not_called()

    def test_an_out_of_bounds_second_click_does_not_clear_an_existing_selection(self):
        network = Mock()
        screen = make_screen(network)
        screen.handle_click(Position(6, 0))

        screen.handle_click(Position(0, 9))

        self.assertTrue(screen.selected.equals(Position(6, 0)))
        network.send.assert_not_called()


class TestHandleRightClick(unittest.TestCase):

    def test_right_click_with_nothing_selected_does_nothing(self):
        network = Mock()
        screen = make_screen(network)

        screen.handle_right_click(Position(6, 0))

        network.send.assert_not_called()

    def test_right_click_on_the_selected_square_sends_a_jump_command_and_clears_selection(self):
        network = Mock()
        screen = make_screen(network)
        screen.handle_click(Position(6, 0))

        screen.handle_right_click(Position(6, 0))

        self.assertIsNone(screen.selected)
        network.send.assert_called_once()
        sent = network.send.call_args.args[0]
        self.assertIsInstance(sent, JumpCommand)
        self.assertEqual(sent.username, "alice")
        self.assertEqual(sent.room_id, "room-1")
        self.assertEqual(sent.position, (6, 0))

    def test_right_click_on_a_different_square_than_selected_does_nothing(self):
        network = Mock()
        screen = make_screen(network)
        screen.handle_click(Position(6, 0))

        screen.handle_right_click(Position(5, 0))

        self.assertTrue(screen.selected.equals(Position(6, 0)))
        network.send.assert_not_called()


if __name__ == "__main__":
    unittest.main()
