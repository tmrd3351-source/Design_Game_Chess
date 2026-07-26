import unittest
from unittest.mock import Mock

from SERVER.config.constants import MOVE_TIME, MOTION_TRANSLATE, MOTION_JUMP
from SERVER.model.position import Position
from SERVER.model.move_result import MoveResult
from SERVER.engine.game_engine import GameEngine


def make_engine():
    board = Mock()
    rule_engine = Mock()
    arbiter = Mock()
    arbiter.game_over = False
    arbiter.is_source_busy.return_value = False
    engine = GameEngine(board, rule_engine, arbiter)
    return engine, board, rule_engine, arbiter


class TestGameEngineConstruction(unittest.TestCase):

    def test_stores_collaborators(self):
        board, rule_engine, arbiter = Mock(), Mock(), Mock()
        engine = GameEngine(board, rule_engine, arbiter)
        self.assertIs(engine.board, board)
        self.assertIs(engine.rule_engine, rule_engine)
        self.assertIs(engine.arbiter, arbiter)

    def test_time_starts_at_zero(self):
        engine, *_ = make_engine()
        self.assertEqual(engine.time, 0)


class TestInsideBoard(unittest.TestCase):

    def test_delegates_to_board_inside_bounds(self):
        engine, board, *_ = make_engine()
        board.inside_bounds.return_value = True
        position = Mock()

        result = engine.inside_board(position)

        self.assertTrue(result)
        board.inside_bounds.assert_called_once_with(position)

    def test_returns_false_when_board_reports_out_of_bounds(self):
        engine, board, *_ = make_engine()
        board.inside_bounds.return_value = False
        self.assertFalse(engine.inside_board(Mock()))


class TestGetPieceColor(unittest.TestCase):

    def test_returns_the_color_of_the_piece_at_the_position(self):
        engine, board, *_ = make_engine()
        piece = Mock()
        piece.get_color.return_value = "w"
        board.get_piece.return_value = piece

        self.assertEqual(engine.get_piece_color(Position(0, 0)), "w")

    def test_returns_none_when_the_square_is_empty(self):
        engine, board, *_ = make_engine()
        board.get_piece.return_value = None

        self.assertIsNone(engine.get_piece_color(Position(0, 0)))


class TestRequestMove(unittest.TestCase):

    def test_game_over_rejects_without_consulting_rules_or_arbiter_busy_state(self):
        engine, board, rule_engine, arbiter = make_engine()
        arbiter.game_over = True

        result = engine.request_move(Position(0, 0), Position(0, 1))

        self.assertFalse(result.is_valid)
        self.assertEqual(result.reason, "game_over")
        rule_engine.check.assert_not_called()
        arbiter.schedule.assert_not_called()

    def test_busy_source_rejects_without_consulting_rules(self):
        engine, board, rule_engine, arbiter = make_engine()
        arbiter.is_source_busy.return_value = True

        result = engine.request_move(Position(0, 0), Position(0, 1))

        self.assertFalse(result.is_valid)
        self.assertEqual(result.reason, "motion_in_progress")
        rule_engine.check.assert_not_called()
        arbiter.schedule.assert_not_called()

    def test_illegal_rule_result_is_returned_and_nothing_is_scheduled(self):
        engine, board, rule_engine, arbiter = make_engine()
        illegal = MoveResult.illegal("illegal_move")
        rule_engine.check.return_value = illegal

        result = engine.request_move(Position(0, 0), Position(0, 1))

        self.assertIs(result, illegal)
        arbiter.schedule.assert_not_called()

    def test_legal_single_square_move_schedules_a_motion_with_no_remaining_route(self):
        engine, board, rule_engine, arbiter = make_engine()
        rule_engine.check.return_value = MoveResult.legal()
        piece = Mock()
        piece.get_kind.return_value = "K"
        board.get_piece.return_value = piece
        source, destination = Position(2, 2), Position(2, 3)

        result = engine.request_move(source, destination)

        self.assertTrue(result.is_valid)
        arbiter.schedule.assert_called_once()
        motion = arbiter.schedule.call_args.args[0]
        self.assertIs(motion.piece, piece)
        self.assertIs(motion.origin, source)
        self.assertIs(motion.source, source)
        self.assertIs(motion.destination, destination)
        self.assertEqual(motion.start_time, 0)
        self.assertEqual(motion.duration, MOVE_TIME)
        self.assertEqual(motion.kind, MOTION_TRANSLATE)
        self.assertEqual(motion.remaining_route, [])

    def test_legal_multi_square_move_schedules_first_leg_with_remaining_route(self):
        engine, board, rule_engine, arbiter = make_engine()
        rule_engine.check.return_value = MoveResult.legal()
        piece = Mock()
        piece.get_kind.return_value = "R"
        board.get_piece.return_value = piece
        source, destination = Position(0, 0), Position(0, 3)

        engine.request_move(source, destination)

        motion = arbiter.schedule.call_args.args[0]
        self.assertEqual((motion.destination.get_row(), motion.destination.get_col()), (0, 1))
        self.assertEqual(
            [(p.get_row(), p.get_col()) for p in motion.remaining_route],
            [(0, 2), (0, 3)],
        )

    def test_returned_result_is_the_legal_result_from_rule_engine(self):
        engine, board, rule_engine, arbiter = make_engine()
        legal = MoveResult.legal()
        rule_engine.check.return_value = legal
        piece = Mock()
        piece.get_kind.return_value = "K"
        board.get_piece.return_value = piece

        result = engine.request_move(Position(0, 0), Position(0, 1))

        self.assertIs(result, legal)

    def test_sequence_number_increments_across_successive_requests(self):
        engine, board, rule_engine, arbiter = make_engine()
        rule_engine.check.return_value = MoveResult.legal()
        piece = Mock()
        piece.get_kind.return_value = "K"
        board.get_piece.return_value = piece

        engine.request_move(Position(0, 0), Position(0, 1))
        engine.request_move(Position(5, 5), Position(5, 6))

        first_motion = arbiter.schedule.call_args_list[0].args[0]
        second_motion = arbiter.schedule.call_args_list[1].args[0]
        self.assertEqual(first_motion.sequence, 1)
        self.assertEqual(second_motion.sequence, 2)

    def test_scheduled_motion_uses_the_engines_current_time_as_start_time(self):
        engine, board, rule_engine, arbiter = make_engine()
        rule_engine.check.return_value = MoveResult.legal()
        piece = Mock()
        piece.get_kind.return_value = "K"
        board.get_piece.return_value = piece
        engine.time = 4000

        engine.request_move(Position(0, 0), Position(0, 1))

        motion = arbiter.schedule.call_args.args[0]
        self.assertEqual(motion.start_time, 4000)


class TestRequestJump(unittest.TestCase):

    def test_game_over_rejects_without_touching_board_or_scheduling(self):
        engine, board, rule_engine, arbiter = make_engine()
        arbiter.game_over = True

        result = engine.request_jump(Position(0, 0))

        self.assertFalse(result.is_valid)
        self.assertEqual(result.reason, "game_over")
        board.get_piece.assert_not_called()
        arbiter.schedule.assert_not_called()

    def test_busy_position_rejects_without_touching_board(self):
        engine, board, rule_engine, arbiter = make_engine()
        arbiter.is_source_busy.return_value = True

        result = engine.request_jump(Position(0, 0))

        self.assertFalse(result.is_valid)
        self.assertEqual(result.reason, "motion_in_progress")
        board.get_piece.assert_not_called()

    def test_empty_square_is_illegal(self):
        engine, board, rule_engine, arbiter = make_engine()
        board.get_piece.return_value = None

        result = engine.request_jump(Position(0, 0))

        self.assertFalse(result.is_valid)
        self.assertEqual(result.reason, "illegal_move")
        arbiter.schedule.assert_not_called()

    def test_occupied_square_schedules_a_same_square_jump_motion(self):
        engine, board, rule_engine, arbiter = make_engine()
        piece = Mock()
        board.get_piece.return_value = piece
        position = Position(3, 3)

        result = engine.request_jump(position)

        self.assertTrue(result.is_valid)
        arbiter.schedule.assert_called_once()
        motion = arbiter.schedule.call_args.args[0]
        self.assertIs(motion.piece, piece)
        self.assertIs(motion.origin, position)
        self.assertIs(motion.source, position)
        self.assertIs(motion.destination, position)
        self.assertEqual(motion.duration, MOVE_TIME)
        self.assertEqual(motion.kind, MOTION_JUMP)

    def test_sequence_number_is_shared_with_request_move_counter(self):
        engine, board, rule_engine, arbiter = make_engine()
        rule_engine.check.return_value = MoveResult.legal()
        piece = Mock()
        piece.get_kind.return_value = "K"
        board.get_piece.return_value = piece

        engine.request_move(Position(0, 0), Position(0, 1))
        engine.request_jump(Position(5, 5))

        jump_motion = arbiter.schedule.call_args.args[0]
        self.assertEqual(jump_motion.sequence, 2)


class TestWaitAndResolve(unittest.TestCase):

    def test_wait_advances_time_by_the_given_amount(self):
        engine, board, rule_engine, arbiter = make_engine()
        engine.wait(500)
        self.assertEqual(engine.time, 500)

    def test_wait_accumulates_across_multiple_calls(self):
        engine, board, rule_engine, arbiter = make_engine()
        engine.wait(500)
        engine.wait(300)
        self.assertEqual(engine.time, 800)

    def test_wait_calls_arbiter_advance_with_the_new_cumulative_time(self):
        engine, board, rule_engine, arbiter = make_engine()
        engine.wait(500)
        engine.wait(300)
        self.assertEqual(
            [call.args[0] for call in arbiter.advance.call_args_list],
            [500, 800],
        )

    def test_resolve_calls_arbiter_advance_with_current_time_unchanged(self):
        engine, board, rule_engine, arbiter = make_engine()
        engine.wait(700)
        arbiter.advance.reset_mock()

        engine.resolve()

        arbiter.advance.assert_called_once_with(700)
        self.assertEqual(engine.time, 700)

    def test_resolve_before_any_wait_advances_with_zero(self):
        engine, board, rule_engine, arbiter = make_engine()
        engine.resolve()
        arbiter.advance.assert_called_once_with(0)


if __name__ == "__main__":
    unittest.main()
