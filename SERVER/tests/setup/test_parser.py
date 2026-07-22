import unittest
from unittest.mock import patch, Mock

from SERVER.setup.parser import parse_input, validate, build_board
from SHARED.config.constants import VALID_TOKENS


def feed(lines):
    """Patches builtins.input to replay `lines` then raise EOFError,
    exactly like piping a finite stdin stream into parse_input()."""
    return patch("builtins.input", side_effect=list(lines) + [EOFError()])


class TestParseInput(unittest.TestCase):

    def test_immediate_eof_returns_empty_tokens_and_commands(self):
        with feed([]):
            tokens, commands = parse_input()
        self.assertEqual(tokens, [])
        self.assertEqual(commands, [])

    def test_board_lines_are_split_into_token_rows(self):
        with feed(["Board:", "wK . .", ". . ."]):
            tokens, commands = parse_input()
        self.assertEqual(tokens, [["wK", ".", "."], [".", ".", "."]])
        self.assertEqual(commands, [])

    def test_commands_after_header_are_collected_verbatim(self):
        with feed(["Board:", "wK . .", "Commands:", "click 50 50", "wait 1000"]):
            tokens, commands = parse_input()
        self.assertEqual(tokens, [["wK", ".", "."]])
        self.assertEqual(commands, ["click 50 50", "wait 1000"])

    def test_blank_lines_inside_board_section_are_skipped(self):
        with feed(["Board:", "wK . .", "", ".  .  ."]):
            tokens, commands = parse_input()
        self.assertEqual(tokens, [["wK", ".", "."], [".", ".", "."]])

    def test_blank_lines_inside_commands_section_are_skipped(self):
        with feed(["Board:", "wK", "Commands:", "print board", "", "wait 500"]):
            tokens, commands = parse_input()
        self.assertEqual(commands, ["print board", "wait 500"])

    def test_lines_before_board_header_are_ignored(self):
        with feed(["some stray junk", "Board:", "wK"]):
            tokens, commands = parse_input()
        self.assertEqual(tokens, [["wK"]])

    def test_lines_are_stripped_of_surrounding_whitespace(self):
        with feed(["Board:", "   wK  .   ."]):
            tokens, commands = parse_input()
        self.assertEqual(tokens, [["wK", ".", "."]])

    def test_missing_commands_header_yields_no_commands(self):
        with feed(["Board:", "wK"]):
            tokens, commands = parse_input()
        self.assertEqual(tokens, [["wK"]])
        self.assertEqual(commands, [])

    def test_reentering_board_header_after_commands_keeps_reading_board(self):
        # Once "Commands:" has been seen, a later "Board:" line sets
        # reading_board back to True *without* clearing reading_commands,
        # so board-parsing wins and further lines go back into tokens.
        with feed(["Board:", "wK", "Commands:", "click 1 1", "Board:", "bK"]):
            tokens, commands = parse_input()
        self.assertEqual(tokens, [["wK"], ["bK"]])
        self.assertEqual(commands, ["click 1 1"])


class TestValidate(unittest.TestCase):

    def test_empty_tokens_is_valid(self):
        self.assertIsNone(validate([]))

    def test_single_row_uniform_valid_tokens_is_valid(self):
        self.assertIsNone(validate([["wK", ".", "bK"]]))

    def test_multiple_rows_same_width_is_valid(self):
        self.assertIsNone(validate([["wK", "."], [".", "bK"]]))

    def test_every_valid_token_is_accepted(self):
        for token in VALID_TOKENS:
            self.assertIsNone(validate([[token]]))

    def test_second_row_wider_than_first_is_width_mismatch(self):
        self.assertEqual(validate([["wK"], [".", "."]]), "ERROR ROW_WIDTH_MISMATCH")

    def test_second_row_narrower_than_first_is_width_mismatch(self):
        self.assertEqual(validate([["wK", "."], ["."]]), "ERROR ROW_WIDTH_MISMATCH")

    def test_unknown_token_is_rejected(self):
        self.assertEqual(validate([["wK", "xZ"]]), "ERROR UNKNOWN_TOKEN")

    def test_unknown_color_prefix_is_rejected(self):
        self.assertEqual(validate([["zK"]]), "ERROR UNKNOWN_TOKEN")

    def test_unknown_kind_suffix_is_rejected(self):
        self.assertEqual(validate([["wZ"]]), "ERROR UNKNOWN_TOKEN")

    def test_width_mismatch_takes_priority_over_unknown_token_on_same_row(self):
        # The offending row itself is both too wide and contains a bad
        # token; width is checked before token validity for that row.
        self.assertEqual(validate([["wK"], ["xZ", "xZ"]]), "ERROR ROW_WIDTH_MISMATCH")

    def test_first_offending_row_wins_when_errors_span_multiple_rows(self):
        # Row 0 has an unknown token; row 1 has a width mismatch. Rows are
        # scanned in order, so row 0's error is returned first.
        self.assertEqual(validate([["xZ"], [".", "."]]), "ERROR UNKNOWN_TOKEN")


class TestBuildBoard(unittest.TestCase):

    def test_empty_tokens_produces_zero_by_zero_board(self):
        board = build_board([])
        self.assertEqual(board.rows, 0)
        self.assertEqual(board.cols, 0)
        self.assertEqual(board.grid, [])

    def test_board_dimensions_match_token_grid(self):
        board = build_board([["wK", ".", "."], [".", ".", "bK"]])
        self.assertEqual(board.rows, 2)
        self.assertEqual(board.cols, 3)

    def test_all_empty_board_has_no_pieces(self):
        board = build_board([[".", "."], [".", "."]])
        for row in range(2):
            for col in range(2):
                self.assertIsNone(board.grid[row][col])

    def test_piece_is_placed_at_matching_row_and_col(self):
        board = build_board([[".", "."], [".", "wK"]])
        piece = board.grid[1][1]
        self.assertIsNotNone(piece)
        self.assertEqual(piece.get_color(), "w")
        self.assertEqual(piece.get_kind(), "K")
        self.assertEqual((piece.get_position().get_row(), piece.get_position().get_col()), (1, 1))

    def test_piece_ids_are_assigned_sequentially_in_row_major_order(self):
        board = build_board([["wK", "bK"], ["wR", "."]])
        self.assertEqual(board.grid[0][0].id, 0)
        self.assertEqual(board.grid[0][1].id, 1)
        self.assertEqual(board.grid[1][0].id, 2)
        self.assertIsNone(board.grid[1][1])

    def test_rectangular_board_wider_than_tall(self):
        board = build_board([["wK", ".", ".", "bK"]])
        self.assertEqual(board.rows, 1)
        self.assertEqual(board.cols, 4)
        self.assertEqual(board.grid[0][0].get_kind(), "K")
        self.assertEqual(board.grid[0][3].get_color(), "b")


class TestBuildBoardIsolatedFromModelClasses(unittest.TestCase):
    """Patches Board/Piece/Position at the point build_board looks them up,
    verifying build_board's own contract without depending on the real
    model implementations (already covered by tests/model)."""

    @patch("setup.parser.Position")
    @patch("setup.parser.Piece")
    @patch("setup.parser.Board")
    def test_constructs_board_with_row_and_col_counts(self, board_cls, piece_cls, position_cls):
        build_board([["wK", "."]])
        board_cls.assert_called_once_with(1, 2)

    @patch("setup.parser.Position")
    @patch("setup.parser.Piece")
    @patch("setup.parser.Board")
    def test_skips_piece_construction_for_empty_cells(self, board_cls, piece_cls, position_cls):
        build_board([[".", "."]])
        piece_cls.assert_not_called()

    @patch("setup.parser.Position")
    @patch("setup.parser.Piece")
    @patch("setup.parser.Board")
    def test_constructs_piece_with_id_color_kind_and_position(self, board_cls, piece_cls, position_cls):
        position_cls.return_value = Mock(name="position(0,1)")

        build_board([[".", "bN"]])

        position_cls.assert_called_once_with(0, 1)
        piece_cls.assert_called_once_with(0, "b", "N", position_cls.return_value)

    @patch("setup.parser.Position")
    @patch("setup.parser.Piece")
    @patch("setup.parser.Board")
    def test_adds_every_constructed_piece_to_the_board(self, board_cls, piece_cls, position_cls):
        board_instance = Mock()
        board_cls.return_value = board_instance
        piece_cls.side_effect = [Mock(name="piece_a"), Mock(name="piece_b")]

        build_board([["wK", "bK"]])

        self.assertEqual(board_instance.add_piece.call_count, 2)


if __name__ == "__main__":
    unittest.main()
