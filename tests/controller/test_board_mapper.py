import unittest

from controller.board_mapper import BoardMapper
from config.constants import CELL_SIZE


class TestBoardMapper(unittest.TestCase):

    def setUp(self):
        self.mapper = BoardMapper()

    def test_origin_pixel_maps_to_origin_cell(self):
        position = self.mapper.to_position(0, 0)
        self.assertEqual(position.get_row(), 0)
        self.assertEqual(position.get_col(), 0)

    def test_center_of_first_cell_maps_to_row_0_col_0(self):
        position = self.mapper.to_position(50, 50)
        self.assertEqual((position.get_row(), position.get_col()), (0, 0))

    def test_x_selects_column_y_selects_row(self):
        # x=250 -> col 2, y=150 -> row 1: make sure the axes aren't swapped.
        position = self.mapper.to_position(250, 150)
        self.assertEqual(position.get_row(), 1)
        self.assertEqual(position.get_col(), 2)

    def test_pixel_just_below_cell_boundary_stays_in_same_cell(self):
        position = self.mapper.to_position(CELL_SIZE - 1, CELL_SIZE - 1)
        self.assertEqual((position.get_row(), position.get_col()), (0, 0))

    def test_pixel_exactly_on_cell_boundary_rolls_into_next_cell(self):
        position = self.mapper.to_position(CELL_SIZE, CELL_SIZE)
        self.assertEqual((position.get_row(), position.get_col()), (1, 1))

    def test_pixel_just_past_boundary_is_in_next_cell(self):
        position = self.mapper.to_position(CELL_SIZE + 1, CELL_SIZE + 1)
        self.assertEqual((position.get_row(), position.get_col()), (1, 1))

    def test_large_pixel_values_map_to_large_cell_indices(self):
        position = self.mapper.to_position(999, 350)
        self.assertEqual(position.get_row(), 3)
        self.assertEqual(position.get_col(), 9)

    def test_negative_x_floors_toward_negative_column(self):
        # Python's // floors toward negative infinity, so a click one
        # pixel to the left of the board lands in column -1, not 0.
        position = self.mapper.to_position(-1, 50)
        self.assertEqual(position.get_col(), -1)

    def test_negative_y_floors_toward_negative_row(self):
        position = self.mapper.to_position(50, -1)
        self.assertEqual(position.get_row(), -1)

    def test_negative_multiple_of_cell_size_maps_exactly(self):
        position = self.mapper.to_position(-CELL_SIZE, -CELL_SIZE)
        self.assertEqual((position.get_row(), position.get_col()), (-1, -1))

    def test_returns_a_new_position_each_call(self):
        first = self.mapper.to_position(50, 50)
        second = self.mapper.to_position(50, 50)
        self.assertIsNot(first, second)
        self.assertTrue(first.equals(second))


if __name__ == "__main__":
    unittest.main()
