import unittest
from unittest.mock import Mock

from SERVER.engine.model.board import Board
from SERVER.engine.model.piece import Piece
from SERVER.engine.model.position import Position
from SERVER.rules.piece_rules import (
    KingRule, QueenRule, BishopRule, KnightRule, RookRule, PawnRule,
)


# King and Knight never look at board or piece at all (single-step moves
# have no path to check); `None` is used in their place deliberately: if a
# future change starts reading board/piece there, these tests fail loudly
# (AttributeError) instead of silently passing.
UNUSED = None


def pos(row, col):
    return Position(row, col)


def empty_board(size=10):
    """A real, empty Board - used for Queen/Bishop/Rook multi-square moves,
    which now call board.is_occupied(...) while walking their path."""
    return Board(size, size)


def _piece_at(row, col, color="b", kind="P"):
    """A throwaway blocker piece for path-clearance tests; kind/color are
    irrelevant since only occupancy is being tested."""
    return Piece(999, color, kind, Position(row, col))


class TestKingRule(unittest.TestCase):

    def setUp(self):
        self.rule = KingRule()

    def test_one_step_orthogonal_is_legal(self):
        self.assertTrue(self.rule.is_legal(UNUSED, UNUSED, pos(2, 2), pos(2, 3)))
        self.assertTrue(self.rule.is_legal(UNUSED, UNUSED, pos(2, 2), pos(1, 2)))

    def test_one_step_diagonal_is_legal(self):
        self.assertTrue(self.rule.is_legal(UNUSED, UNUSED, pos(2, 2), pos(3, 3)))
        self.assertTrue(self.rule.is_legal(UNUSED, UNUSED, pos(2, 2), pos(1, 1)))

    def test_staying_on_the_same_square_is_legal_by_this_rule_alone(self):
        # KingRule itself has no same-square guard; RuleEngine rejects that
        # case separately before consulting the rule.
        self.assertTrue(self.rule.is_legal(UNUSED, UNUSED, pos(2, 2), pos(2, 2)))

    def test_two_steps_orthogonal_is_illegal(self):
        self.assertFalse(self.rule.is_legal(UNUSED, UNUSED, pos(2, 2), pos(2, 4)))

    def test_two_steps_diagonal_is_illegal(self):
        self.assertFalse(self.rule.is_legal(UNUSED, UNUSED, pos(2, 2), pos(4, 4)))

    def test_knight_shaped_jump_is_illegal(self):
        self.assertFalse(self.rule.is_legal(UNUSED, UNUSED, pos(2, 2), pos(4, 3)))


class TestQueenRule(unittest.TestCase):

    def setUp(self):
        self.rule = QueenRule()

    def test_horizontal_move_any_distance_is_legal(self):
        self.assertTrue(self.rule.is_legal(empty_board(), UNUSED, pos(0, 0), pos(0, 6)))

    def test_vertical_move_any_distance_is_legal(self):
        self.assertTrue(self.rule.is_legal(empty_board(), UNUSED, pos(0, 0), pos(6, 0)))

    def test_diagonal_move_any_distance_is_legal(self):
        self.assertTrue(self.rule.is_legal(empty_board(), UNUSED, pos(1, 1), pos(4, 4)))

    def test_same_square_is_legal_by_this_rule_alone(self):
        self.assertTrue(self.rule.is_legal(UNUSED, UNUSED, pos(2, 2), pos(2, 2)))

    def test_knight_shaped_jump_is_illegal(self):
        self.assertFalse(self.rule.is_legal(UNUSED, UNUSED, pos(0, 0), pos(1, 2)))

    def test_off_diagonal_non_straight_move_is_illegal(self):
        self.assertFalse(self.rule.is_legal(UNUSED, UNUSED, pos(0, 0), pos(2, 5)))

    def test_horizontal_move_blocked_by_piece_in_the_middle_is_illegal(self):
        board = empty_board()
        board.add_piece(_piece_at(0, 3))
        self.assertFalse(self.rule.is_legal(board, UNUSED, pos(0, 0), pos(0, 6)))

    def test_diagonal_move_blocked_by_piece_in_the_middle_is_illegal(self):
        board = empty_board()
        board.add_piece(_piece_at(2, 2))
        self.assertFalse(self.rule.is_legal(board, UNUSED, pos(0, 0), pos(4, 4)))

    def test_move_is_legal_when_only_the_destination_square_is_occupied(self):
        # The path-clear check is exclusive of the destination; an occupant
        # sitting there is a capture/blocked-landing question for other code,
        # not something QueenRule.is_legal itself needs to reject.
        board = empty_board()
        board.add_piece(_piece_at(0, 6))
        self.assertTrue(self.rule.is_legal(board, UNUSED, pos(0, 0), pos(0, 6)))


class TestBishopRule(unittest.TestCase):

    def setUp(self):
        self.rule = BishopRule()

    def test_diagonal_move_one_step_is_legal(self):
        self.assertTrue(self.rule.is_legal(UNUSED, UNUSED, pos(2, 2), pos(3, 3)))

    def test_diagonal_move_long_distance_is_legal(self):
        self.assertTrue(self.rule.is_legal(empty_board(), UNUSED, pos(0, 0), pos(6, 6)))

    def test_same_square_is_legal_by_this_rule_alone(self):
        self.assertTrue(self.rule.is_legal(UNUSED, UNUSED, pos(2, 2), pos(2, 2)))

    def test_horizontal_move_is_illegal(self):
        self.assertFalse(self.rule.is_legal(UNUSED, UNUSED, pos(2, 2), pos(2, 5)))

    def test_vertical_move_is_illegal(self):
        self.assertFalse(self.rule.is_legal(UNUSED, UNUSED, pos(2, 2), pos(5, 2)))

    def test_off_diagonal_move_is_illegal(self):
        self.assertFalse(self.rule.is_legal(UNUSED, UNUSED, pos(0, 0), pos(2, 3)))

    def test_diagonal_move_blocked_by_piece_in_the_middle_is_illegal(self):
        board = empty_board()
        board.add_piece(_piece_at(2, 2))
        self.assertFalse(self.rule.is_legal(board, UNUSED, pos(0, 0), pos(4, 4)))


class TestKnightRule(unittest.TestCase):

    def setUp(self):
        self.rule = KnightRule()

    def test_two_by_one_l_shape_is_legal(self):
        self.assertTrue(self.rule.is_legal(UNUSED, UNUSED, pos(2, 2), pos(4, 3)))

    def test_one_by_two_l_shape_is_legal(self):
        self.assertTrue(self.rule.is_legal(UNUSED, UNUSED, pos(2, 2), pos(3, 4)))

    def test_all_eight_knight_offsets_are_legal(self):
        offsets = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]
        for dr, dc in offsets:
            with self.subTest(dr=dr, dc=dc):
                self.assertTrue(self.rule.is_legal(UNUSED, UNUSED, pos(4, 4), pos(4 + dr, 4 + dc)))

    def test_diagonal_move_is_illegal(self):
        self.assertFalse(self.rule.is_legal(UNUSED, UNUSED, pos(2, 2), pos(3, 3)))

    def test_straight_move_is_illegal(self):
        self.assertFalse(self.rule.is_legal(UNUSED, UNUSED, pos(2, 2), pos(2, 4)))

    def test_same_square_is_illegal(self):
        self.assertFalse(self.rule.is_legal(UNUSED, UNUSED, pos(2, 2), pos(2, 2)))

    def test_three_by_one_is_illegal(self):
        self.assertFalse(self.rule.is_legal(UNUSED, UNUSED, pos(2, 2), pos(5, 3)))


class TestRookRule(unittest.TestCase):

    def setUp(self):
        self.rule = RookRule()

    def test_horizontal_move_any_distance_is_legal(self):
        self.assertTrue(self.rule.is_legal(empty_board(), UNUSED, pos(3, 0), pos(3, 7)))

    def test_vertical_move_any_distance_is_legal(self):
        self.assertTrue(self.rule.is_legal(empty_board(), UNUSED, pos(0, 3), pos(7, 3)))

    def test_same_square_is_legal_by_this_rule_alone(self):
        self.assertTrue(self.rule.is_legal(UNUSED, UNUSED, pos(2, 2), pos(2, 2)))

    def test_diagonal_move_is_illegal(self):
        self.assertFalse(self.rule.is_legal(UNUSED, UNUSED, pos(0, 0), pos(3, 3)))

    def test_arbitrary_move_is_illegal(self):
        self.assertFalse(self.rule.is_legal(UNUSED, UNUSED, pos(0, 0), pos(2, 5)))

    def test_horizontal_move_blocked_by_piece_in_the_middle_is_illegal(self):
        board = empty_board()
        board.add_piece(_piece_at(3, 4))
        self.assertFalse(self.rule.is_legal(board, UNUSED, pos(3, 0), pos(3, 7)))

    def test_vertical_move_blocked_by_piece_in_the_middle_is_illegal(self):
        board = empty_board()
        board.add_piece(_piece_at(4, 3))
        self.assertFalse(self.rule.is_legal(board, UNUSED, pos(0, 3), pos(7, 3)))

    def test_adjacent_square_move_needs_no_board_lookup(self):
        # A single-square rook move has no intermediate square at all, so
        # the path-clear walk never touches the board.
        self.assertTrue(self.rule.is_legal(UNUSED, UNUSED, pos(3, 3), pos(3, 4)))


def make_board(rows, occupant_by_position=None):
    """Mock board exposing what PawnRule (and, for the double-step,
    _path_is_clear) read: .rows, .get_piece(position) and
    .is_occupied(position). occupant_by_position maps (row, col) -> piece."""
    occupant_by_position = occupant_by_position or {}
    board = Mock()
    board.rows = rows

    def get_piece(position):
        return occupant_by_position.get((position.get_row(), position.get_col()))

    board.get_piece.side_effect = get_piece
    board.is_occupied.side_effect = lambda position: get_piece(position) is not None
    return board


def make_piece(color):
    piece = Mock()
    piece.get_color.return_value = color
    return piece


class TestPawnRuleForwardStep(unittest.TestCase):

    def setUp(self):
        self.rule = PawnRule()

    def test_white_single_step_forward_to_empty_square_is_legal(self):
        board = make_board(rows=8)
        piece = make_piece("w")
        # white moves toward decreasing row (direction = -1)
        self.assertTrue(self.rule.is_legal(board, piece, pos(4, 4), pos(3, 4)))

    def test_black_single_step_forward_to_empty_square_is_legal(self):
        board = make_board(rows=8)
        piece = make_piece("b")
        # black moves toward increasing row (direction = +1)
        self.assertTrue(self.rule.is_legal(board, piece, pos(4, 4), pos(5, 4)))

    def test_white_single_step_backward_is_illegal(self):
        board = make_board(rows=8)
        piece = make_piece("w")
        self.assertFalse(self.rule.is_legal(board, piece, pos(4, 4), pos(5, 4)))

    def test_single_step_forward_onto_occupied_square_is_illegal_even_if_enemy(self):
        occupant = make_piece("b")
        board = make_board(rows=8, occupant_by_position={(3, 4): occupant})
        piece = make_piece("w")
        self.assertFalse(self.rule.is_legal(board, piece, pos(4, 4), pos(3, 4)))

    def test_single_step_forward_onto_occupied_square_is_illegal_for_own_piece(self):
        occupant = make_piece("w")
        board = make_board(rows=8, occupant_by_position={(3, 4): occupant})
        piece = make_piece("w")
        self.assertFalse(self.rule.is_legal(board, piece, pos(4, 4), pos(3, 4)))

    def test_sideways_move_is_illegal(self):
        board = make_board(rows=8)
        piece = make_piece("w")
        self.assertFalse(self.rule.is_legal(board, piece, pos(4, 4), pos(4, 5)))


class TestPawnRuleDoubleStep(unittest.TestCase):

    def setUp(self):
        self.rule = PawnRule()

    def test_white_double_step_from_start_row_to_empty_square_is_legal(self):
        board = make_board(rows=4)
        piece = make_piece("w")
        # white start row is board.rows - 1 (the bottom edge)
        self.assertTrue(self.rule.is_legal(board, piece, pos(3, 1), pos(1, 1)))

    def test_black_double_step_from_start_row_to_empty_square_is_legal(self):
        board = make_board(rows=4)
        piece = make_piece("b")
        # black start row is always 0, regardless of board size
        self.assertTrue(self.rule.is_legal(board, piece, pos(0, 1), pos(2, 1)))

    def test_white_double_step_from_one_row_off_start_is_illegal(self):
        board = make_board(rows=4)
        piece = make_piece("w")
        self.assertFalse(self.rule.is_legal(board, piece, pos(2, 1), pos(0, 1)))

    def test_black_double_step_from_one_row_off_start_is_illegal(self):
        board = make_board(rows=4)
        piece = make_piece("b")
        self.assertFalse(self.rule.is_legal(board, piece, pos(1, 1), pos(3, 1)))

    def test_white_start_row_scales_with_board_size(self):
        # An 8-row board puts white's start row at 7, not 3.
        board = make_board(rows=8)
        piece = make_piece("w")
        self.assertTrue(self.rule.is_legal(board, piece, pos(7, 1), pos(5, 1)))
        self.assertFalse(self.rule.is_legal(board, piece, pos(3, 1), pos(1, 1)))

    def test_double_step_onto_occupied_destination_is_illegal(self):
        occupant = make_piece("b")
        board = make_board(rows=4, occupant_by_position={(1, 1): occupant})
        piece = make_piece("w")
        self.assertFalse(self.rule.is_legal(board, piece, pos(3, 1), pos(1, 1)))

    def test_double_step_is_blocked_by_a_piece_on_the_intermediate_square(self):
        # The double-step now runs the same path-clear check as sliding
        # pieces, so a blocker on the square the pawn passes over (not just
        # the final destination) makes the whole move illegal.
        blocker = make_piece("b")
        board = make_board(rows=4, occupant_by_position={(2, 1): blocker})
        piece = make_piece("w")
        self.assertFalse(self.rule.is_legal(board, piece, pos(3, 1), pos(1, 1)))

    def test_double_step_wrong_distance_is_illegal(self):
        board = make_board(rows=4)
        piece = make_piece("w")
        self.assertFalse(self.rule.is_legal(board, piece, pos(3, 1), pos(0, 1)))


class TestPawnRuleDiagonalCapture(unittest.TestCase):

    def setUp(self):
        self.rule = PawnRule()

    def test_diagonal_capture_of_enemy_piece_is_legal(self):
        enemy = make_piece("b")
        board = make_board(rows=8, occupant_by_position={(3, 5): enemy})
        piece = make_piece("w")
        self.assertTrue(self.rule.is_legal(board, piece, pos(4, 4), pos(3, 5)))

    def test_diagonal_capture_to_the_left_is_legal(self):
        enemy = make_piece("b")
        board = make_board(rows=8, occupant_by_position={(3, 3): enemy})
        piece = make_piece("w")
        self.assertTrue(self.rule.is_legal(board, piece, pos(4, 4), pos(3, 3)))

    def test_diagonal_move_onto_empty_square_is_illegal(self):
        board = make_board(rows=8)
        piece = make_piece("w")
        self.assertFalse(self.rule.is_legal(board, piece, pos(4, 4), pos(3, 5)))

    def test_diagonal_move_onto_own_piece_is_illegal(self):
        own = make_piece("w")
        board = make_board(rows=8, occupant_by_position={(3, 5): own})
        piece = make_piece("w")
        self.assertFalse(self.rule.is_legal(board, piece, pos(4, 4), pos(3, 5)))

    def test_diagonal_move_two_columns_over_is_illegal(self):
        enemy = make_piece("b")
        board = make_board(rows=8, occupant_by_position={(3, 6): enemy})
        piece = make_piece("w")
        self.assertFalse(self.rule.is_legal(board, piece, pos(4, 4), pos(3, 6)))


class TestPawnRuleUnmatchedShapes(unittest.TestCase):

    def setUp(self):
        self.rule = PawnRule()

    def test_knight_shaped_move_is_illegal(self):
        board = make_board(rows=8)
        piece = make_piece("w")
        self.assertFalse(self.rule.is_legal(board, piece, pos(4, 4), pos(2, 5)))

    def test_same_square_is_illegal(self):
        board = make_board(rows=8)
        piece = make_piece("w")
        self.assertFalse(self.rule.is_legal(board, piece, pos(4, 4), pos(4, 4)))


if __name__ == "__main__":
    unittest.main()
