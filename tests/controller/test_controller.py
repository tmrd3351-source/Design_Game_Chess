import unittest
from unittest.mock import Mock, call

from controller.controller import Controller
from model.game_state import GameState


def make_controller(inside_board=True):
    game_engine = Mock()
    game_engine.inside_board.return_value = inside_board
    board_mapper = Mock()
    controller = Controller(game_engine, board_mapper)
    return controller, game_engine, board_mapper


class TestControllerConstruction(unittest.TestCase):

    def test_stores_collaborators(self):
        game_engine, board_mapper = Mock(), Mock()
        controller = Controller(game_engine, board_mapper)
        self.assertIs(controller.game_engine, game_engine)
        self.assertIs(controller.board_mapper, board_mapper)

    def test_starts_with_nothing_selected(self):
        controller, *_ = make_controller()
        self.assertIsNone(controller.selected)

    def test_default_command_handlers_cover_the_four_known_commands(self):
        controller, *_ = make_controller()
        self.assertEqual(
            set(controller.command_handlers.keys()),
            {"print", "wait", "click", "jump"},
        )

    def test_custom_command_handlers_are_used_when_provided(self):
        custom_handler = Mock()
        game_engine, board_mapper = Mock(), Mock()
        controller = Controller(game_engine, board_mapper,
                                 command_handlers={"foo": custom_handler})

        controller.apply_command("foo bar")

        custom_handler.assert_called_once_with(["foo", "bar"])

    def test_empty_dict_command_handlers_falls_back_to_default(self):
        # `command_handlers or {...}` treats {} as falsy, so passing an
        # explicit empty dict silently reinstates the default handlers
        # instead of leaving the controller with no commands at all.
        game_engine, board_mapper = Mock(), Mock()
        controller = Controller(game_engine, board_mapper,
                                 command_handlers={})

        controller.apply_command("print board")

        game_engine.resolve.assert_called_once()


class TestApplyCommandDispatch(unittest.TestCase):

    def test_empty_command_string_does_nothing(self):
        controller, game_engine, board_mapper = make_controller()
        controller.apply_command("")
        board_mapper.to_position.assert_not_called()

    def test_empty_command_string_returns_none(self):
        controller, *_ = make_controller()
        self.assertIsNone(controller.apply_command(""))

    def test_whitespace_only_command_does_nothing(self):
        controller, game_engine, *_ = make_controller()
        controller.apply_command("    ")
        game_engine.resolve.assert_not_called()

    def test_unknown_command_word_is_ignored(self):
        controller, game_engine, *_ = make_controller()
        controller.apply_command("teleport 1 2")
        game_engine.resolve.assert_not_called()
        game_engine.wait.assert_not_called()
        game_engine.request_move.assert_not_called()
        game_engine.request_jump.assert_not_called()

    def test_unknown_command_word_returns_none(self):
        controller, *_ = make_controller()
        self.assertIsNone(controller.apply_command("teleport 1 2"))

    def test_print_command_resolves_the_engine(self):
        controller, game_engine, board_mapper = make_controller()

        controller.apply_command("print board")

        game_engine.resolve.assert_called_once()

    def test_print_command_returns_the_current_game_state(self):
        controller, game_engine, board_mapper = make_controller()
        game_engine.board = "the_board"
        game_engine.arbiter.winner = "w"
        game_engine.arbiter.game_over = True
        game_engine.arbiter.motions = ["a_motion"]

        state = controller.apply_command("print board")

        self.assertIsInstance(state, GameState)
        self.assertEqual(state.board, "the_board")
        self.assertEqual(state.winner, "w")
        self.assertTrue(state.game_over)
        self.assertEqual(state.motions, ["a_motion"])

    def test_print_command_resolves_before_building_the_returned_state(self):
        controller, game_engine, board_mapper = make_controller()
        manager = Mock()
        manager.attach_mock(game_engine.resolve, "resolve")
        manager.attach_mock(game_engine.board, "board")

        controller.apply_command("print board")

        self.assertEqual(manager.mock_calls[0], call.resolve())

    def test_other_commands_return_none(self):
        controller, game_engine, board_mapper = make_controller()
        board_mapper.to_position.return_value = Mock()

        self.assertIsNone(controller.apply_command("wait 100"))
        self.assertIsNone(controller.apply_command("click 50 50"))
        self.assertIsNone(controller.apply_command("jump 50 50"))

    def test_wait_command_advances_engine_time_as_int(self):
        controller, game_engine, *_ = make_controller()
        controller.apply_command("wait 1500")
        game_engine.wait.assert_called_once_with(1500)

    def test_wait_command_missing_argument_is_ignored(self):
        controller, game_engine, *_ = make_controller()
        controller.apply_command("wait")
        game_engine.wait.assert_not_called()

    def test_wait_command_with_extra_argument_is_ignored(self):
        controller, game_engine, *_ = make_controller()
        controller.apply_command("wait 100 200")
        game_engine.wait.assert_not_called()

    def test_wait_command_with_non_numeric_argument_raises(self):
        controller, *_ = make_controller()
        with self.assertRaises(ValueError):
            controller.apply_command("wait soon")

    def test_click_command_dispatches_to_handle_click_with_ints(self):
        controller, game_engine, board_mapper = make_controller()
        board_mapper.to_position.return_value = Mock()
        controller.apply_command("click 50 150")
        board_mapper.to_position.assert_called_once_with(50, 150)

    def test_click_command_missing_argument_is_ignored(self):
        controller, game_engine, board_mapper = make_controller()
        controller.apply_command("click 50")
        board_mapper.to_position.assert_not_called()

    def test_click_command_with_extra_argument_is_ignored(self):
        controller, game_engine, board_mapper = make_controller()
        controller.apply_command("click 50 50 50")
        board_mapper.to_position.assert_not_called()

    def test_jump_command_dispatches_to_handle_jump_with_ints(self):
        controller, game_engine, board_mapper = make_controller()
        board_mapper.to_position.return_value = Mock()
        controller.apply_command("jump 50 150")
        board_mapper.to_position.assert_called_once_with(50, 150)

    def test_jump_command_missing_argument_is_ignored(self):
        controller, game_engine, board_mapper = make_controller()
        controller.apply_command("jump 50")
        board_mapper.to_position.assert_not_called()


class TestGetState(unittest.TestCase):

    def test_returns_a_game_state_built_from_the_engine_and_arbiter(self):
        controller, game_engine, board_mapper = make_controller()
        game_engine.board = "the_board"
        game_engine.arbiter.winner = "b"
        game_engine.arbiter.game_over = False
        game_engine.arbiter.motions = ["a_motion"]

        state = controller.get_state()

        self.assertIsInstance(state, GameState)
        self.assertEqual(state.board, "the_board")
        self.assertEqual(state.winner, "b")
        self.assertFalse(state.game_over)
        self.assertEqual(state.motions, ["a_motion"])


class TestHandleWait(unittest.TestCase):

    def test_delegates_to_game_engine_wait(self):
        controller, game_engine, *_ = make_controller()
        controller.handle_wait(500)
        game_engine.wait.assert_called_once_with(500)


class TestHandleMove(unittest.TestCase):

    def test_delegates_to_game_engine_request_move_with_source_and_destination(self):
        controller, game_engine, *_ = make_controller()
        source = Mock()
        destination = Mock()

        controller.handle_move(source, destination)

        game_engine.request_move.assert_called_once_with(source, destination)

    def test_does_not_touch_current_selection(self):
        controller, game_engine, *_ = make_controller()
        selected = Mock()
        controller.selected = selected

        controller.handle_move(Mock(), Mock())

        self.assertIs(controller.selected, selected)


class TestHandleClick(unittest.TestCase):

    def test_click_outside_board_is_ignored_when_nothing_selected(self):
        controller, game_engine, board_mapper = make_controller(inside_board=False)
        position = Mock()
        board_mapper.to_position.return_value = position

        controller.handle_click(9999, 9999)

        game_engine.can_select.assert_not_called()
        self.assertIsNone(controller.selected)

    def test_click_outside_board_leaves_existing_selection_untouched(self):
        controller, game_engine, board_mapper = make_controller(inside_board=True)
        already_selected = Mock()
        controller.selected = already_selected
        game_engine.inside_board.return_value = False

        controller.handle_click(9999, 9999)

        game_engine.is_same_side.assert_not_called()
        game_engine.request_move.assert_not_called()
        self.assertIs(controller.selected, already_selected)

    def test_click_on_selectable_piece_selects_it(self):
        controller, game_engine, board_mapper = make_controller()
        position = Mock()
        board_mapper.to_position.return_value = position
        game_engine.can_select.return_value = True

        controller.handle_click(50, 50)

        self.assertIs(controller.selected, position)
        game_engine.request_move.assert_not_called()

    def test_click_on_non_selectable_square_selects_nothing(self):
        controller, game_engine, board_mapper = make_controller()
        board_mapper.to_position.return_value = Mock()
        game_engine.can_select.return_value = False

        controller.handle_click(50, 50)

        self.assertIsNone(controller.selected)

    def test_click_same_side_piece_while_selectable_switches_selection(self):
        controller, game_engine, board_mapper = make_controller()
        source = Mock()
        controller.selected = source
        new_position = Mock()
        board_mapper.to_position.return_value = new_position
        game_engine.is_same_side.return_value = True
        game_engine.can_select.return_value = True

        controller.handle_click(150, 50)

        game_engine.is_same_side.assert_called_once_with(source, new_position)
        self.assertIs(controller.selected, new_position)
        game_engine.request_move.assert_not_called()

    def test_click_same_side_piece_while_not_selectable_clears_selection(self):
        controller, game_engine, board_mapper = make_controller()
        source = Mock()
        controller.selected = source
        new_position = Mock()
        board_mapper.to_position.return_value = new_position
        game_engine.is_same_side.return_value = True
        game_engine.can_select.return_value = False

        controller.handle_click(150, 50)

        self.assertIsNone(controller.selected)
        game_engine.request_move.assert_not_called()

    def test_click_on_opposite_side_or_empty_square_requests_move(self):
        controller, game_engine, board_mapper = make_controller()
        source = Mock()
        controller.selected = source
        destination = Mock()
        board_mapper.to_position.return_value = destination
        game_engine.is_same_side.return_value = False

        controller.handle_click(250, 50)

        game_engine.request_move.assert_called_once_with(source, destination)

    def test_click_requesting_move_always_clears_selection_afterward(self):
        controller, game_engine, board_mapper = make_controller()
        controller.selected = Mock()
        board_mapper.to_position.return_value = Mock()
        game_engine.is_same_side.return_value = False

        controller.handle_click(250, 50)

        self.assertIsNone(controller.selected)

    def test_click_requesting_move_clears_selection_even_if_move_illegal(self):
        # request_move's return value is never inspected; selection is
        # cleared unconditionally once a move has been requested.
        controller, game_engine, board_mapper = make_controller()
        controller.selected = Mock()
        board_mapper.to_position.return_value = Mock()
        game_engine.is_same_side.return_value = False
        game_engine.request_move.return_value = Mock(is_valid=False, reason="illegal_move")

        controller.handle_click(250, 50)

        self.assertIsNone(controller.selected)


class TestHandleJump(unittest.TestCase):

    def test_jump_outside_board_does_not_request_jump(self):
        controller, game_engine, board_mapper = make_controller(inside_board=False)

        controller.handle_jump(9999, 9999)

        game_engine.request_jump.assert_not_called()

    def test_jump_inside_board_requests_jump_at_mapped_position(self):
        controller, game_engine, board_mapper = make_controller()
        position = Mock()
        board_mapper.to_position.return_value = position

        controller.handle_jump(50, 150)

        board_mapper.to_position.assert_called_once_with(50, 150)
        game_engine.request_jump.assert_called_once_with(position)

    def test_jump_does_not_touch_current_selection(self):
        controller, game_engine, board_mapper = make_controller()
        selected = Mock()
        controller.selected = selected
        board_mapper.to_position.return_value = Mock()

        controller.handle_jump(50, 150)

        self.assertIs(controller.selected, selected)

    def test_jump_with_no_prior_selection_leaves_selection_none(self):
        controller, game_engine, board_mapper = make_controller()
        board_mapper.to_position.return_value = Mock()

        controller.handle_jump(50, 150)

        self.assertIsNone(controller.selected)


if __name__ == "__main__":
    unittest.main()
