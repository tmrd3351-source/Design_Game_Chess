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


class TestHandleJump(unittest.TestCase):

    def test_delegates_to_game_engine_request_jump_with_the_position(self):
        game_engine = Mock()
        controller = Controller(game_engine)
        position = Mock()

        controller.handle_jump(position)

        game_engine.request_jump.assert_called_once_with(position)


if __name__ == "__main__":
    unittest.main()
