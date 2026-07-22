import unittest
from unittest.mock import Mock

from SERVER.model.game_state import GameState
from SERVER.model.position import Position


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

    def test_move_log_defaults_to_an_empty_list(self):
        state = GameState(Mock(), None, False)
        self.assertEqual(state.move_log, [])

    def test_move_log_can_be_provided_explicitly(self):
        move_log = [{"color": "w"}]
        state = GameState(Mock(), None, False, move_log=move_log)
        self.assertEqual(state.move_log, move_log)

    def test_score_defaults_to_zero_for_both_colors(self):
        state = GameState(Mock(), None, False)
        self.assertEqual(state.score, {"w": 0, "b": 0})

    def test_score_can_be_provided_explicitly(self):
        state = GameState(Mock(), None, False, score={"w": 9, "b": 3})
        self.assertEqual(state.score, {"w": 9, "b": 3})


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
            "move_log": [],
            "score": {"w": 0, "b": 0},
        })

    def test_empty_motions_list_serializes_to_empty_list(self):
        board = Mock()
        board.to_dict.return_value = {"rows": 8, "cols": 8, "pieces": []}
        state = GameState(board, None, False)

        self.assertEqual(state.to_dict()["motions"], [])

    def test_move_log_entries_serialize_source_and_destination_positions(self):
        board = Mock()
        board.to_dict.return_value = {"rows": 8, "cols": 8, "pieces": []}
        move_log = [{
            "color": "w", "kind": "R",
            "source": Position(6, 0), "destination": Position(5, 0),
            "captured": ["P"],
        }]
        state = GameState(board, None, False, move_log=move_log)

        self.assertEqual(state.to_dict()["move_log"], [{
            "color": "w", "kind": "R",
            "source": {"row": 6, "col": 0}, "destination": {"row": 5, "col": 0},
            "captured": ["P"],
        }])

    def test_score_is_included_as_is(self):
        board = Mock()
        board.to_dict.return_value = {"rows": 8, "cols": 8, "pieces": []}
        state = GameState(board, None, False, score={"w": 4, "b": 1})

        self.assertEqual(state.to_dict()["score"], {"w": 4, "b": 1})


if __name__ == "__main__":
    unittest.main()
