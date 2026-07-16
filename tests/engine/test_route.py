import unittest

from model.position import Position
from engine.route import compute_route


def pos(row, col):
    return Position(row, col)


def as_pairs(route):
    return [(p.get_row(), p.get_col()) for p in route]


class TestComputeRouteSingleStepKinds(unittest.TestCase):

    def test_king_one_square_returns_only_the_destination(self):
        route = compute_route("K", pos(2, 2), pos(2, 3))
        self.assertEqual(as_pairs(route), [(2, 3)])

    def test_king_ignores_distance_and_still_returns_only_destination(self):
        # compute_route does not validate legality; it just refuses to
        # split K/N moves into legs, however far apart the squares are.
        route = compute_route("K", pos(0, 0), pos(7, 7))
        self.assertEqual(as_pairs(route), [(7, 7)])

    def test_knight_l_shape_returns_only_the_destination(self):
        route = compute_route("N", pos(4, 4), pos(2, 5))
        self.assertEqual(as_pairs(route), [(2, 5)])

    def test_king_returned_route_contains_the_actual_destination_object(self):
        destination = pos(2, 3)
        route = compute_route("K", pos(2, 2), destination)
        self.assertIs(route[0], destination)


class TestComputeRouteSlidingKinds(unittest.TestCase):

    def test_rook_horizontal_multi_square_lists_every_intermediate_square(self):
        route = compute_route("R", pos(0, 0), pos(0, 3))
        self.assertEqual(as_pairs(route), [(0, 1), (0, 2), (0, 3)])

    def test_rook_horizontal_moving_left_lists_squares_in_travel_order(self):
        route = compute_route("R", pos(0, 5), pos(0, 2))
        self.assertEqual(as_pairs(route), [(0, 4), (0, 3), (0, 2)])

    def test_rook_vertical_multi_square(self):
        route = compute_route("R", pos(0, 0), pos(3, 0))
        self.assertEqual(as_pairs(route), [(1, 0), (2, 0), (3, 0)])

    def test_rook_vertical_moving_up_lists_squares_in_travel_order(self):
        route = compute_route("R", pos(5, 0), pos(2, 0))
        self.assertEqual(as_pairs(route), [(4, 0), (3, 0), (2, 0)])

    def test_bishop_diagonal_down_right(self):
        route = compute_route("B", pos(0, 0), pos(3, 3))
        self.assertEqual(as_pairs(route), [(1, 1), (2, 2), (3, 3)])

    def test_bishop_diagonal_up_left(self):
        route = compute_route("B", pos(3, 3), pos(0, 0))
        self.assertEqual(as_pairs(route), [(2, 2), (1, 1), (0, 0)])

    def test_bishop_diagonal_down_left(self):
        route = compute_route("B", pos(0, 3), pos(3, 0))
        self.assertEqual(as_pairs(route), [(1, 2), (2, 1), (3, 0)])

    def test_bishop_diagonal_up_right(self):
        route = compute_route("B", pos(3, 0), pos(0, 3))
        self.assertEqual(as_pairs(route), [(2, 1), (1, 2), (0, 3)])

    def test_queen_horizontal_uses_same_stepping_as_rook(self):
        route = compute_route("Q", pos(2, 0), pos(2, 4))
        self.assertEqual(as_pairs(route), [(2, 1), (2, 2), (2, 3), (2, 4)])

    def test_queen_diagonal_uses_same_stepping_as_bishop(self):
        route = compute_route("Q", pos(0, 0), pos(2, 2))
        self.assertEqual(as_pairs(route), [(1, 1), (2, 2)])

    def test_adjacent_square_sliding_move_has_only_the_destination(self):
        route = compute_route("R", pos(3, 3), pos(3, 4))
        self.assertEqual(as_pairs(route), [(3, 4)])

    def test_route_last_element_is_the_actual_destination_object(self):
        destination = pos(0, 3)
        route = compute_route("R", pos(0, 0), destination)
        self.assertIs(route[-1], destination)

    def test_same_square_sliding_move_returns_single_element_route(self):
        # dr == dc == 0, so both step values are 0 and the walk loop's
        # condition is already true before it ever runs.
        route = compute_route("R", pos(2, 2), pos(2, 2))
        self.assertEqual(as_pairs(route), [(2, 2)])

    def test_pawn_single_step_returns_only_the_destination(self):
        # Pawn is not a SINGLE_STEP_KIND, but a 1-square move still steps
        # directly onto the destination with no intermediate square.
        route = compute_route("P", pos(4, 4), pos(3, 4))
        self.assertEqual(as_pairs(route), [(3, 4)])

    def test_pawn_double_step_includes_the_intermediate_square(self):
        route = compute_route("P", pos(3, 4), pos(1, 4))
        self.assertEqual(as_pairs(route), [(2, 4), (1, 4)])


if __name__ == "__main__":
    unittest.main()
