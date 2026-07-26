import unittest
from unittest.mock import Mock

from SERVER.controller.controller import Controller
from SERVER.model.game_state import GameState


class TestControllerConstruction(unittest.TestCase):

    def test_stores_game_engine(self):
        game_engine = Mock()
        controller = Controller(game_engine)
        self.assertIs(controller.game_engine, game_engine)


class TestGetState(unittest.TestCase):

    def test_returns_a_game_state_built_from_the_engine_and_arbiter(self):
        game_engine = Mock()
        game_engine.board = "the_board"
        game_engine.arbiter.winner = "b"
        game_engine.arbiter.game_over = False
        game_engine.arbiter.motions = ["a_motion"]
        game_engine.arbiter.move_log = ["a_move"]
        game_engine.arbiter.get_score.return_value = {"w": 3, "b": 0}
        controller = Controller(game_engine)

        state = controller.get_state()

        self.assertIsInstance(state, GameState)
        self.assertEqual(state.board, "the_board")
        self.assertEqual(state.winner, "b")
        self.assertFalse(state.game_over)
        self.assertEqual(state.motions, ["a_motion"])
        self.assertEqual(state.move_log, ["a_move"])
        self.assertEqual(state.score, {"w": 3, "b": 0})


class TestHandleWait(unittest.TestCase):

    def test_delegates_to_game_engine_wait(self):
        game_engine = Mock()
        controller = Controller(game_engine)
        controller.handle_wait(500)
        game_engine.wait.assert_called_once_with(500)


class TestHandleMove(unittest.TestCase):

    def test_delegates_to_game_engine_request_move_with_source_and_destination(self):
        game_engine = Mock()
        controller = Controller(game_engine)
        source = Mock()
        destination = Mock()

        controller.handle_move(source, destination)

        game_engine.request_move.assert_called_once_with(source, destination)

    def test_returns_whatever_game_engine_request_move_returns(self):
        game_engine = Mock()
        game_engine.request_move.return_value = "the_result"
        controller = Controller(game_engine)

        result = controller.handle_move(Mock(), Mock())

        self.assertEqual(result, "the_result")


class TestHandleJump(unittest.TestCase):

    def test_delegates_to_game_engine_request_jump_with_the_position(self):
        game_engine = Mock()
        controller = Controller(game_engine)
        position = Mock()

        controller.handle_jump(position)

        game_engine.request_jump.assert_called_once_with(position)

    def test_returns_whatever_game_engine_request_jump_returns(self):
        game_engine = Mock()
        game_engine.request_jump.return_value = "the_result"
        controller = Controller(game_engine)

        result = controller.handle_jump(Mock())

        self.assertEqual(result, "the_result")


class TestInsideBoard(unittest.TestCase):

    def test_delegates_to_game_engine_inside_board(self):
        game_engine = Mock()
        game_engine.inside_board.return_value = True
        controller = Controller(game_engine)
        position = Mock()

        result = controller.inside_board(position)

        self.assertTrue(result)
        game_engine.inside_board.assert_called_once_with(position)


class TestCanControlPiece(unittest.TestCase):

    def test_false_when_position_is_out_of_bounds(self):
        game_engine = Mock()
        game_engine.inside_board.return_value = False
        controller = Controller(game_engine)

        self.assertFalse(controller.can_control_piece("w", Mock()))
        game_engine.get_piece_color.assert_not_called()

    def test_true_when_the_pieces_color_matches(self):
        game_engine = Mock()
        game_engine.inside_board.return_value = True
        game_engine.get_piece_color.return_value = "w"
        controller = Controller(game_engine)
        position = Mock()

        result = controller.can_control_piece("w", position)

        self.assertTrue(result)
        game_engine.get_piece_color.assert_called_once_with(position)

    def test_false_when_the_pieces_color_does_not_match(self):
        game_engine = Mock()
        game_engine.inside_board.return_value = True
        game_engine.get_piece_color.return_value = "b"
        controller = Controller(game_engine)

        self.assertFalse(controller.can_control_piece("w", Mock()))

    def test_false_when_the_square_is_empty(self):
        game_engine = Mock()
        game_engine.inside_board.return_value = True
        game_engine.get_piece_color.return_value = None
        controller = Controller(game_engine)

        self.assertFalse(controller.can_control_piece("w", Mock()))


if __name__ == "__main__":
    unittest.main()
