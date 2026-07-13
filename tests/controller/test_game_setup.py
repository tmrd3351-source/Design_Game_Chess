import unittest
from unittest.mock import patch

from controller.game_setup import GameSetup


class TestGameSetup(unittest.TestCase):

    @patch("controller.game_setup.build_board")
    @patch("controller.game_setup.validate")
    @patch("controller.game_setup.parse_input")
    def test_valid_input_returns_board_and_commands(self, parse_input, validate, build_board):
        parse_input.return_value = ([["wK"]], ["print board"])
        validate.return_value = None
        build_board.return_value = "the_board"

        result = GameSetup().load()

        self.assertEqual(result, ("the_board", ["print board"]))

    @patch("controller.game_setup.build_board")
    @patch("controller.game_setup.validate")
    @patch("controller.game_setup.parse_input")
    def test_valid_input_builds_board_from_parsed_tokens(self, parse_input, validate, build_board):
        parse_input.return_value = ([["wK"]], [])
        validate.return_value = None
        build_board.return_value = "the_board"

        GameSetup().load()

        build_board.assert_called_once_with([["wK"]])

    @patch("controller.game_setup.build_board")
    @patch("controller.game_setup.validate")
    @patch("controller.game_setup.parse_input")
    def test_validate_is_called_with_parsed_tokens(self, parse_input, validate, build_board):
        parse_input.return_value = (["tokens"], ["commands"])
        validate.return_value = None
        build_board.return_value = "board"

        GameSetup().load()

        validate.assert_called_once_with(["tokens"])

    @patch("controller.game_setup.build_board")
    @patch("controller.game_setup.validate")
    @patch("controller.game_setup.parse_input")
    @patch("builtins.print")
    def test_invalid_input_prints_error_and_returns_none(self, mock_print, parse_input, validate, build_board):
        parse_input.return_value = ([["xZ"]], [])
        validate.return_value = "ERROR UNKNOWN_TOKEN"

        result = GameSetup().load()

        self.assertIsNone(result)
        mock_print.assert_called_once_with("ERROR UNKNOWN_TOKEN")

    @patch("controller.game_setup.build_board")
    @patch("controller.game_setup.validate")
    @patch("controller.game_setup.parse_input")
    @patch("builtins.print")
    def test_invalid_input_never_builds_a_board(self, mock_print, parse_input, validate, build_board):
        parse_input.return_value = ([["xZ"]], [])
        validate.return_value = "ERROR ROW_WIDTH_MISMATCH"

        GameSetup().load()

        build_board.assert_not_called()

    @patch("controller.game_setup.build_board")
    @patch("controller.game_setup.validate")
    @patch("controller.game_setup.parse_input")
    def test_empty_string_error_is_falsy_and_treated_as_valid(self, parse_input, validate, build_board):
        # `if error:` treats "" the same as None: build_board still runs.
        parse_input.return_value = ([["wK"]], [])
        validate.return_value = ""
        build_board.return_value = "the_board"

        result = GameSetup().load()

        self.assertEqual(result, ("the_board", []))
        build_board.assert_called_once_with([["wK"]])


if __name__ == "__main__":
    unittest.main()
