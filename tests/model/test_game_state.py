import unittest
from unittest.mock import Mock

from model.game_state import GameState


class TestGameStateConstruction(unittest.TestCase):

    def test_stores_board_winner_and_game_over(self):
        board = Mock()
        state = GameState(board, "w", True)
        self.assertIs(state.board, board)
        self.assertEqual(state.winner, "w")
        self.assertTrue(state.game_over)

    def test_motions_defaults_to_an_empty_list(self):
        state = GameState(Mock(), None, False)
        self.assertEqual(state.motions, [])

    def test_motions_can_be_provided_explicitly(self):
        motions = [Mock(), Mock()]
        state = GameState(Mock(), None, False, motions)
        self.assertEqual(state.motions, motions)


class TestGameStateToDict(unittest.TestCase):

    def test_returns_a_plain_json_safe_snapshot(self):
        board = Mock()
        board.to_dict.return_value = {"rows": 8, "cols": 8, "pieces": []}
        motion = Mock()
        motion.to_dict.return_value = {"piece_id": 1}
        state = GameState(board, "b", True, [motion])

        self.assertEqual(state.to_dict(), {
            "board": {"rows": 8, "cols": 8, "pieces": []},
            "winner": "b",
            "game_over": True,
            "motions": [{"piece_id": 1}],
        })

    def test_empty_motions_list_serializes_to_empty_list(self):
        board = Mock()
        board.to_dict.return_value = {"rows": 8, "cols": 8, "pieces": []}
        state = GameState(board, None, False)

        self.assertEqual(state.to_dict()["motions"], [])


if __name__ == "__main__":
    unittest.main()
