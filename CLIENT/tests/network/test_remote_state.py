import unittest

from CLIENT.network.remote_state import RemotePiece, RemoteBoard, RemoteMotion, RemoteGameState
from CLIENT.model.position import Position
from CLIENT.config.constants import STATE_IDLE, REST_NONE, MOTION_TRANSLATE
from SERVER.engine.model.board import Board
from SERVER.engine.model.piece import Piece
from SERVER.engine.model.motion import Motion
from SERVER.engine.model.game_state import GameState


def make_piece_dict(piece_id=1, color="w", kind="K", row=0, col=0):
    return {
        "id": piece_id,
        "color": color,
        "kind": kind,
        "position": {"row": row, "col": col},
        "state": STATE_IDLE,
        "rest_type": REST_NONE,
        "rest_progress": 0.0,
    }


class TestRemotePiece(unittest.TestCase):

    def test_exposes_the_same_getters_as_the_real_piece(self):
        piece = RemotePiece(make_piece_dict(piece_id=3, color="b", kind="Q", row=2, col=4))

        self.assertEqual(piece.id, 3)
        self.assertEqual(piece.get_color(), "b")
        self.assertEqual(piece.get_kind(), "Q")
        self.assertEqual((piece.get_position().get_row(), piece.get_position().get_col()), (2, 4))
        self.assertEqual(piece.get_state(), STATE_IDLE)
        self.assertEqual(piece.get_rest_type(), REST_NONE)
        self.assertEqual(piece.get_rest_progress(), 0.0)


class TestRemoteBoard(unittest.TestCase):

    def test_get_piece_finds_a_piece_at_its_cell(self):
        board = RemoteBoard({
            "rows": 3, "cols": 3,
            "pieces": [make_piece_dict(piece_id=1, row=1, col=2)],
        })

        found = board.get_piece(Position(1, 2))

        self.assertIsNotNone(found)
        self.assertEqual(found.id, 1)

    def test_get_piece_returns_none_for_an_empty_cell(self):
        board = RemoteBoard({"rows": 3, "cols": 3, "pieces": []})
        self.assertIsNone(board.get_piece(Position(0, 0)))

    def test_find_piece_by_id(self):
        board = RemoteBoard({
            "rows": 3, "cols": 3,
            "pieces": [make_piece_dict(piece_id=7, row=0, col=0)],
        })

        self.assertEqual(board.find_piece_by_id(7).id, 7)
        self.assertIsNone(board.find_piece_by_id(999))

    def test_rows_and_cols_are_stored(self):
        board = RemoteBoard({"rows": 8, "cols": 8, "pieces": []})
        self.assertEqual(board.rows, 8)
        self.assertEqual(board.cols, 8)


class TestRemoteMotion(unittest.TestCase):

    def test_exposes_the_same_fields_as_the_real_motion(self):
        piece = RemotePiece(make_piece_dict())
        data = {
            "piece_id": 1,
            "origin": {"row": 0, "col": 0},
            "source": {"row": 0, "col": 1},
            "destination": {"row": 0, "col": 2},
            "kind": MOTION_TRANSLATE,
            "sequence": 5,
            "progress": 0.5,
        }

        motion = RemoteMotion(data, piece)

        self.assertIs(motion.piece, piece)
        self.assertEqual(motion.kind, MOTION_TRANSLATE)
        self.assertEqual(motion.sequence, 5)
        self.assertEqual(motion.progress, 0.5)
        self.assertEqual((motion.source.get_row(), motion.source.get_col()), (0, 1))
        self.assertEqual((motion.destination.get_row(), motion.destination.get_col()), (0, 2))


class TestRemoteGameState(unittest.TestCase):

    def test_exposes_winner_and_game_over(self):
        state = RemoteGameState({"board": {"rows": 1, "cols": 1, "pieces": []},
                                  "winner": "w", "game_over": True, "motions": []})
        self.assertEqual(state.winner, "w")
        self.assertTrue(state.game_over)

    def test_move_log_and_score_default_to_empty_when_absent(self):
        state = RemoteGameState({"board": {"rows": 1, "cols": 1, "pieces": []},
                                  "winner": None, "game_over": False, "motions": []})
        self.assertEqual(state.move_log, [])
        self.assertEqual(state.score, {"w": 0, "b": 0})

    def test_move_log_entries_expose_positions_like_the_real_move_log(self):
        data = {
            "board": {"rows": 1, "cols": 1, "pieces": []},
            "winner": None, "game_over": False, "motions": [],
            "move_log": [{
                "color": "w", "kind": "R",
                "source": {"row": 6, "col": 0}, "destination": {"row": 5, "col": 0},
                "captured": ["P"],
            }],
            "score": {"w": 1, "b": 0},
        }

        state = RemoteGameState(data)

        entry = state.move_log[0]
        self.assertEqual(entry["color"], "w")
        self.assertEqual(entry["kind"], "R")
        self.assertEqual((entry["source"].get_row(), entry["source"].get_col()), (6, 0))
        self.assertEqual((entry["destination"].get_row(), entry["destination"].get_col()), (5, 0))
        self.assertEqual(entry["captured"], ["P"])
        self.assertEqual(state.score, {"w": 1, "b": 0})

    def test_motions_reference_the_same_piece_instance_as_the_board(self):
        data = {
            "board": {"rows": 3, "cols": 3, "pieces": [make_piece_dict(piece_id=1, row=0, col=0)]},
            "winner": None,
            "game_over": False,
            "motions": [{
                "piece_id": 1,
                "origin": {"row": 0, "col": 0}, "source": {"row": 0, "col": 0},
                "destination": {"row": 0, "col": 1},
                "kind": MOTION_TRANSLATE, "sequence": 1, "progress": 0.1,
            }],
        }

        state = RemoteGameState(data)

        board_piece = state.board.get_piece(Position(0, 0))
        self.assertIs(state.motions[0].piece, board_piece)

    def test_round_trips_a_real_gamestate_to_dict_snapshot(self):
        # No hand-written dicts: proves RemoteGameState correctly consumes
        # the exact shape GameState.to_dict() actually produces.
        board = Board(8, 8)
        piece = Piece(1, "w", "R", Position(6, 0))
        board.add_piece(piece)
        motion = Motion(piece, Position(6, 0), Position(6, 0), Position(5, 0),
                         start_time=0, duration=1000, kind=MOTION_TRANSLATE, sequence=1)
        motion.update(500)
        real_state = GameState(board, "w", True, [motion])

        remote = RemoteGameState(real_state.to_dict())

        self.assertEqual(remote.board.rows, 8)
        self.assertEqual(remote.board.cols, 8)
        self.assertEqual(remote.winner, "w")
        self.assertTrue(remote.game_over)
        self.assertEqual(len(remote.motions), 1)
        found_piece = remote.board.get_piece(Position(6, 0))
        self.assertEqual(found_piece.get_kind(), "R")
        self.assertIs(remote.motions[0].piece, found_piece)
        self.assertAlmostEqual(remote.motions[0].progress, 0.5)


if __name__ == "__main__":
    unittest.main()
