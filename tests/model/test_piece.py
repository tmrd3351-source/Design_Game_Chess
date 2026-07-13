import unittest
from unittest.mock import Mock

from model.piece import Piece


class TestPiece(unittest.TestCase):

    def test_constructor_stores_id_color_kind(self):
        position = Mock()
        piece = Piece(7, "w", "K", position)
        self.assertEqual(piece.id, 7)
        self.assertEqual(piece.color, "w")
        self.assertEqual(piece.kind, "K")

    def test_constructor_starts_idle(self):
        piece = Piece(1, "b", "P", Mock())
        self.assertEqual(piece.get_state(), "idle")

    def test_get_position_returns_constructor_value(self):
        position = Mock()
        piece = Piece(1, "w", "Q", position)
        self.assertIs(piece.get_position(), position)

    def test_set_position_overwrites_position(self):
        piece = Piece(1, "w", "Q", Mock())
        new_position = Mock()
        piece.set_position(new_position)
        self.assertIs(piece.get_position(), new_position)

    def test_get_color_returns_constructor_value(self):
        piece = Piece(1, "b", "R", Mock())
        self.assertEqual(piece.get_color(), "b")

    def test_get_kind_returns_constructor_value(self):
        piece = Piece(1, "w", "N", Mock())
        self.assertEqual(piece.get_kind(), "N")

    def test_set_kind_overwrites_kind(self):
        piece = Piece(1, "w", "P", Mock())
        piece.set_kind("Q")
        self.assertEqual(piece.get_kind(), "Q")

    def test_set_kind_used_for_pawn_promotion_keeps_color_and_position(self):
        position = Mock()
        piece = Piece(1, "w", "P", position)
        piece.set_kind("Q")
        self.assertEqual(piece.get_kind(), "Q")
        self.assertEqual(piece.get_color(), "w")
        self.assertIs(piece.get_position(), position)

    def test_get_state_returns_current_state(self):
        piece = Piece(1, "w", "R", Mock())
        self.assertEqual(piece.get_state(), "idle")

    def test_set_state_overwrites_state(self):
        piece = Piece(1, "w", "R", Mock())
        piece.set_state("moving")
        self.assertEqual(piece.get_state(), "moving")

    def test_set_state_can_transition_back_to_idle(self):
        piece = Piece(1, "w", "R", Mock())
        piece.set_state("moving")
        piece.set_state("idle")
        self.assertEqual(piece.get_state(), "idle")

    def test_set_state_accepts_arbitrary_string_without_validation(self):
        piece = Piece(1, "w", "R", Mock())
        piece.set_state("anything")
        self.assertEqual(piece.get_state(), "anything")

    def test_two_pieces_are_independent_instances(self):
        piece_a = Piece(1, "w", "K", Mock())
        piece_b = Piece(2, "b", "K", Mock())
        piece_a.set_state("moving")
        piece_b.set_kind("Q")
        self.assertEqual(piece_a.get_state(), "moving")
        self.assertEqual(piece_b.get_state(), "idle")
        self.assertEqual(piece_a.get_kind(), "K")
        self.assertEqual(piece_b.get_kind(), "Q")


if __name__ == "__main__":
    unittest.main()
