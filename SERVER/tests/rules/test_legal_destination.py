import unittest
from unittest.mock import Mock

from SERVER.rules.legal_destination import LegalDestination

# NOTE: grep across the repo shows LegalDestination.check is not called
# anywhere else in production code - it appears to be dead/unused code.
# These tests document its existing, standalone contract in case it is
# wired in later, without asserting anything about where it's used.


def make_board(inside_bounds, occupant=None):
    board = Mock()
    board.inside_bounds.return_value = inside_bounds
    board.get_piece.return_value = occupant
    return board


class TestLegalDestination(unittest.TestCase):

    def test_position_outside_board_is_illegal(self):
        board = make_board(inside_bounds=False)
        self.assertFalse(LegalDestination.check(board, Mock(), "w"))

    def test_position_outside_board_is_illegal_even_if_occupant_would_be_capturable(self):
        occupant = Mock()
        occupant.get_color.return_value = "b"
        board = make_board(inside_bounds=False, occupant=occupant)
        self.assertFalse(LegalDestination.check(board, Mock(), "w"))

    def test_empty_square_inside_board_is_legal(self):
        board = make_board(inside_bounds=True, occupant=None)
        self.assertTrue(LegalDestination.check(board, Mock(), "w"))

    def test_square_occupied_by_enemy_is_legal(self):
        occupant = Mock()
        occupant.get_color.return_value = "b"
        board = make_board(inside_bounds=True, occupant=occupant)
        self.assertTrue(LegalDestination.check(board, Mock(), "w"))

    def test_square_occupied_by_own_color_is_illegal(self):
        occupant = Mock()
        occupant.get_color.return_value = "w"
        board = make_board(inside_bounds=True, occupant=occupant)
        self.assertFalse(LegalDestination.check(board, Mock(), "w"))

    def test_is_callable_as_a_staticmethod_without_an_instance(self):
        board = make_board(inside_bounds=True, occupant=None)
        # Calling via the class (no instance) must work, confirming this
        # is genuinely a staticmethod and not accidentally an instance method.
        self.assertTrue(LegalDestination.check(board, Mock(), "w"))


if __name__ == "__main__":
    unittest.main()
