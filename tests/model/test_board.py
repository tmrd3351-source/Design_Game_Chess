import unittest
from unittest.mock import Mock

from model.board import Board
from model.position import Position


def make_piece(position):
    """A Mock standing in for model.piece.Piece, isolating Board tests
    from Piece's real implementation. get_position/set_position are wired
    together (like the real Piece) since Board.move_piece depends on
    set_position actually being reflected by a later get_position call."""
    piece = Mock()
    piece.get_position.return_value = position

    def set_position(new_position):
        piece.get_position.return_value = new_position

    piece.set_position.side_effect = set_position
    return piece


class TestBoardConstruction(unittest.TestCase):

    def test_grid_has_requested_dimensions(self):
        board = Board(3, 4)
        self.assertEqual(len(board.grid), 3)
        for row in board.grid:
            self.assertEqual(len(row), 4)

    def test_grid_starts_empty(self):
        board = Board(2, 2)
        for row in board.grid:
            for cell in row:
                self.assertIsNone(cell)

    def test_rows_and_cols_are_stored(self):
        board = Board(5, 7)
        self.assertEqual(board.rows, 5)
        self.assertEqual(board.cols, 7)

    def test_rows_are_independent_lists(self):
        board = Board(2, 2)
        board.grid[0][0] = "sentinel"
        self.assertIsNone(board.grid[1][0])

    def test_zero_size_board_has_empty_grid(self):
        board = Board(0, 0)
        self.assertEqual(board.grid, [])


class TestBoardAddPiece(unittest.TestCase):

    def test_add_piece_places_piece_at_its_own_position(self):
        board = Board(3, 3)
        position = Position(1, 2)
        piece = make_piece(position)

        board.add_piece(piece)

        self.assertIs(board.grid[1][2], piece)

    def test_add_piece_overwrites_existing_occupant(self):
        board = Board(3, 3)
        position = Position(0, 0)
        first = make_piece(position)
        second = make_piece(position)

        board.add_piece(first)
        board.add_piece(second)

        self.assertIs(board.get_piece(position), second)


class TestBoardRemovePiece(unittest.TestCase):

    def test_remove_piece_clears_the_cell(self):
        board = Board(3, 3)
        position = Position(2, 2)
        board.add_piece(make_piece(position))

        board.remove_piece(position)

        self.assertIsNone(board.get_piece(position))

    def test_remove_piece_on_already_empty_cell_is_a_no_op(self):
        board = Board(3, 3)
        position = Position(0, 0)

        board.remove_piece(position)

        self.assertIsNone(board.get_piece(position))


class TestBoardMovePiece(unittest.TestCase):

    def test_move_piece_relocates_piece_to_destination(self):
        board = Board(3, 3)
        source = Position(0, 0)
        destination = Position(2, 2)
        piece = make_piece(source)
        board.add_piece(piece)

        board.move_piece(source, destination)

        self.assertIs(board.get_piece(destination), piece)

    def test_move_piece_clears_the_source_cell(self):
        board = Board(3, 3)
        source = Position(0, 0)
        destination = Position(2, 2)
        piece = make_piece(source)
        board.add_piece(piece)

        board.move_piece(source, destination)

        self.assertIsNone(board.get_piece(source))

    def test_move_piece_updates_piece_position_to_destination(self):
        board = Board(3, 3)
        source = Position(0, 0)
        destination = Position(2, 2)
        piece = make_piece(source)
        board.add_piece(piece)

        board.move_piece(source, destination)

        piece.set_position.assert_called_once_with(destination)

    def test_move_piece_reads_destination_from_piece_after_set_position(self):
        # add_piece places the piece using piece.get_position(), so
        # move_piece must call set_position(destination) *before* re-adding
        # the piece, otherwise it would land back on the source cell.
        board = Board(3, 3)
        source = Position(0, 0)
        destination = Position(2, 2)
        piece = make_piece(source)
        board.add_piece(piece)

        board.move_piece(source, destination)

        self.assertIs(board.get_piece(destination), piece)
        self.assertIsNone(board.get_piece(source))

    def test_move_piece_to_same_square_keeps_piece_in_place(self):
        board = Board(3, 3)
        position = Position(1, 1)
        piece = make_piece(position)
        board.add_piece(piece)

        board.move_piece(position, position)

        self.assertIs(board.get_piece(position), piece)


class TestBoardGetPiece(unittest.TestCase):

    def test_get_piece_returns_none_for_empty_cell(self):
        board = Board(3, 3)
        self.assertIsNone(board.get_piece(Position(1, 1)))

    def test_get_piece_returns_the_occupant(self):
        board = Board(3, 3)
        position = Position(1, 1)
        piece = make_piece(position)
        board.add_piece(piece)

        self.assertIs(board.get_piece(position), piece)


class TestBoardIsOccupied(unittest.TestCase):

    def test_is_occupied_false_for_empty_cell(self):
        board = Board(3, 3)
        self.assertFalse(board.is_occupied(Position(0, 0)))

    def test_is_occupied_true_for_occupied_cell(self):
        board = Board(3, 3)
        position = Position(0, 0)
        board.add_piece(make_piece(position))
        self.assertTrue(board.is_occupied(position))

    def test_is_occupied_false_after_removal(self):
        board = Board(3, 3)
        position = Position(0, 0)
        board.add_piece(make_piece(position))
        board.remove_piece(position)
        self.assertFalse(board.is_occupied(position))


class TestBoardInsideBounds(unittest.TestCase):

    def test_top_left_corner_is_inside(self):
        board = Board(3, 3)
        self.assertTrue(board.inside_bounds(Position(0, 0)))

    def test_bottom_right_corner_is_inside(self):
        board = Board(3, 4)
        self.assertTrue(board.inside_bounds(Position(2, 3)))

    def test_row_equal_to_rows_is_outside(self):
        board = Board(3, 3)
        self.assertFalse(board.inside_bounds(Position(3, 0)))

    def test_col_equal_to_cols_is_outside(self):
        board = Board(3, 3)
        self.assertFalse(board.inside_bounds(Position(0, 3)))

    def test_negative_row_is_outside(self):
        board = Board(3, 3)
        self.assertFalse(board.inside_bounds(Position(-1, 0)))

    def test_negative_col_is_outside(self):
        board = Board(3, 3)
        self.assertFalse(board.inside_bounds(Position(0, -1)))

    def test_far_out_of_range_position_is_outside(self):
        board = Board(3, 3)
        self.assertFalse(board.inside_bounds(Position(100, 100)))

    def test_zero_size_board_rejects_every_position(self):
        board = Board(0, 0)
        self.assertFalse(board.inside_bounds(Position(0, 0)))

    def test_rectangular_board_respects_independent_row_and_col_limits(self):
        board = Board(2, 5)
        self.assertTrue(board.inside_bounds(Position(1, 4)))
        self.assertFalse(board.inside_bounds(Position(2, 4)))
        self.assertFalse(board.inside_bounds(Position(1, 5)))


if __name__ == "__main__":
    unittest.main()
