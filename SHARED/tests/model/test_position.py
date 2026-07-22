import unittest

from SHARED.model.position import Position


class TestPosition(unittest.TestCase):

    def test_get_row_returns_constructor_value(self):
        position = Position(3, 5)
        self.assertEqual(position.get_row(), 3)

    def test_get_col_returns_constructor_value(self):
        position = Position(3, 5)
        self.assertEqual(position.get_col(), 5)

    def test_equals_true_for_same_row_and_col(self):
        self.assertTrue(Position(2, 4).equals(Position(2, 4)))

    def test_equals_false_for_different_row(self):
        self.assertFalse(Position(2, 4).equals(Position(3, 4)))

    def test_equals_false_for_different_col(self):
        self.assertFalse(Position(2, 4).equals(Position(2, 5)))

    def test_equals_false_for_different_row_and_col(self):
        self.assertFalse(Position(2, 4).equals(Position(9, 9)))

    def test_equals_is_symmetric(self):
        a = Position(1, 1)
        b = Position(1, 1)
        self.assertEqual(a.equals(b), b.equals(a))

    def test_equals_with_negative_coordinates(self):
        self.assertTrue(Position(-1, -1).equals(Position(-1, -1)))

    def test_equals_with_zero_coordinates(self):
        self.assertTrue(Position(0, 0).equals(Position(0, 0)))

    def test_equals_accepts_any_object_with_row_and_col_attributes(self):
        class DuckPosition:
            row = 7
            col = 8

        self.assertTrue(Position(7, 8).equals(DuckPosition()))

    def test_to_dict_returns_row_and_col(self):
        self.assertEqual(Position(3, 5).to_dict(), {"row": 3, "col": 5})


if __name__ == "__main__":
    unittest.main()
