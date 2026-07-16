import itertools
import unittest
from unittest.mock import Mock

from config.constants import (
    MOVE_COOLDOWN_TIME, JUMP_COOLDOWN_TIME, REST_NONE, REST_SHORT, REST_LONG,
    STATE_IDLE, STATE_MOVING, STATE_JUMPING, MOTION_TRANSLATE, MOTION_JUMP,
)
from model.board import Board
from model.piece import Piece
from model.position import Position
from model.motion import Motion
from engine.real_time_arbiter import RealTimeArbiter


_ids = itertools.count(1)


def make_piece(color, kind, row, col):
    return Piece(next(_ids), color, kind, Position(row, col))


def make_arbiter(rows=3, cols=3, rules=None):
    board = Board(rows, cols)
    rule_engine = Mock()
    rule_engine.rules = rules if rules is not None else {}
    arbiter = RealTimeArbiter(board, rule_engine)
    return arbiter, board, rule_engine


def allow_rule():
    """A Mock piece-rule whose is_legal always returns True."""
    rule = Mock()
    rule.is_legal.return_value = True
    return rule


def translate_motion(piece, source, destination, start_time=0, duration=1000,
                      remaining_route=None, sequence=1):
    return Motion(piece, piece.get_position(), source, destination, start_time, duration,
                  kind=MOTION_TRANSLATE, sequence=sequence, remaining_route=remaining_route)


def jump_motion(piece, position, start_time=0, duration=1000, sequence=1):
    return Motion(piece, position, position, position, start_time, duration,
                  kind=MOTION_JUMP, sequence=sequence)


class TestSchedule(unittest.TestCase):

    def test_sets_piece_state_to_moving(self):
        arbiter, board, rule_engine = make_arbiter()
        piece = make_piece("w", "R", 0, 0)
        board.add_piece(piece)

        arbiter.schedule(translate_motion(piece, Position(0, 0), Position(0, 1)))

        self.assertEqual(piece.get_state(), STATE_MOVING)

    def test_sets_piece_state_to_jumping_for_a_jump_motion(self):
        arbiter, board, rule_engine = make_arbiter()
        piece = make_piece("w", "K", 1, 1)
        board.add_piece(piece)

        arbiter.schedule(jump_motion(piece, Position(1, 1)))

        self.assertEqual(piece.get_state(), STATE_JUMPING)

    def test_appends_motion_to_motions_list(self):
        arbiter, board, rule_engine = make_arbiter()
        piece = make_piece("w", "R", 0, 0)
        board.add_piece(piece)
        motion = translate_motion(piece, Position(0, 0), Position(0, 1))

        arbiter.schedule(motion)

        self.assertIn(motion, arbiter.motions)


class TestIsSourceBusy(unittest.TestCase):

    def test_false_when_no_motions(self):
        arbiter, board, rule_engine = make_arbiter()
        self.assertFalse(arbiter.is_source_busy(Position(0, 0)))

    def test_true_when_a_translate_motion_originates_there(self):
        arbiter, board, rule_engine = make_arbiter()
        piece = make_piece("w", "R", 0, 0)
        board.add_piece(piece)
        arbiter.schedule(translate_motion(piece, Position(0, 0), Position(0, 1)))

        self.assertTrue(arbiter.is_source_busy(Position(0, 0)))

    def test_true_when_a_jump_motion_originates_there(self):
        arbiter, board, rule_engine = make_arbiter()
        piece = make_piece("w", "K", 1, 1)
        board.add_piece(piece)
        arbiter.schedule(jump_motion(piece, Position(1, 1)))

        self.assertTrue(arbiter.is_source_busy(Position(1, 1)))

    def test_false_for_an_unrelated_position(self):
        arbiter, board, rule_engine = make_arbiter()
        piece = make_piece("w", "R", 0, 0)
        board.add_piece(piece)
        arbiter.schedule(translate_motion(piece, Position(0, 0), Position(0, 1)))

        self.assertFalse(arbiter.is_source_busy(Position(2, 2)))


class TestAdvanceScheduling(unittest.TestCase):

    def test_advance_with_no_motions_does_nothing(self):
        arbiter, board, rule_engine = make_arbiter()
        arbiter.advance(1000)  # must not raise

    def test_motion_not_yet_due_stays_scheduled(self):
        arbiter, board, rule_engine = make_arbiter(rules={"R": allow_rule()})
        piece = make_piece("w", "R", 0, 0)
        board.add_piece(piece)
        motion = translate_motion(piece, Position(0, 0), Position(0, 1), start_time=0, duration=1000)
        arbiter.schedule(motion)

        arbiter.advance(500)

        self.assertIn(motion, arbiter.motions)
        self.assertEqual(board.get_piece(Position(0, 0)), piece)

    def test_pending_motions_get_progress_updated_even_when_not_due(self):
        arbiter, board, rule_engine = make_arbiter(rules={"R": allow_rule()})
        piece = make_piece("w", "R", 0, 0)
        board.add_piece(piece)
        motion = translate_motion(piece, Position(0, 0), Position(0, 1), start_time=0, duration=1000)
        arbiter.schedule(motion)

        arbiter.advance(250)

        self.assertAlmostEqual(motion.progress, 0.25)

    def test_due_motion_is_resolved_and_removed(self):
        arbiter, board, rule_engine = make_arbiter(rules={"R": allow_rule()})
        piece = make_piece("w", "R", 0, 0)
        board.add_piece(piece)
        motion = translate_motion(piece, Position(0, 0), Position(0, 1), start_time=0, duration=1000)
        arbiter.schedule(motion)

        arbiter.advance(1000)

        self.assertNotIn(motion, arbiter.motions)
        self.assertEqual(board.get_piece(Position(0, 1)), piece)

    def test_tie_break_prefers_translate_over_jump_at_same_finish_time(self):
        arbiter, board, rule_engine = make_arbiter(rules={"R": allow_rule()})
        mover = make_piece("w", "R", 0, 0)
        jumper = make_piece("w", "K", 2, 2)
        board.add_piece(mover)
        board.add_piece(jumper)
        # Both due at the same time; if the jump resolved first it would
        # still just idle the jumper, but the ordering itself is what this
        # test pins: translate motions are due-sorted ahead of jumps.
        arbiter.schedule(jump_motion(jumper, Position(2, 2), start_time=0, duration=1000, sequence=1))
        arbiter.schedule(translate_motion(mover, Position(0, 0), Position(0, 1), start_time=0, duration=1000, sequence=2))

        arbiter.advance(1000)

        self.assertEqual(board.get_piece(Position(0, 1)), mover)
        self.assertEqual(jumper.get_state(), STATE_IDLE)

    def test_tie_break_prefers_lower_sequence_among_same_kind(self):
        arbiter, board, rule_engine = make_arbiter(rules={"R": allow_rule()})
        piece_a = make_piece("w", "R", 0, 0)
        piece_b = make_piece("b", "R", 2, 2)
        board.add_piece(piece_a)
        board.add_piece(piece_b)
        order = []
        motion_a = translate_motion(piece_a, Position(0, 0), Position(0, 1), start_time=0, duration=1000, sequence=5)
        motion_b = translate_motion(piece_b, Position(2, 2), Position(2, 1), start_time=0, duration=1000, sequence=1)
        arbiter.schedule(motion_a)
        arbiter.schedule(motion_b)

        original_resolve = arbiter._resolve

        def tracking_resolve(motion):
            order.append(motion.sequence)
            return original_resolve(motion)

        arbiter._resolve = tracking_resolve
        arbiter.advance(1000)

        self.assertEqual(order, [1, 5])

    def test_cascading_multi_leg_move_completes_within_a_single_advance_call(self):
        # A 2-square rook move whose total duration (2000ms) fits inside one
        # advance() call must resolve both legs, not just the first.
        arbiter, board, rule_engine = make_arbiter(cols=4, rules={"R": allow_rule()})
        piece = make_piece("w", "R", 0, 0)
        board.add_piece(piece)
        route = [Position(0, 1), Position(0, 2)]
        motion = translate_motion(piece, Position(0, 0), route[0], start_time=0, duration=1000,
                                   remaining_route=[route[1]])
        arbiter.schedule(motion)

        arbiter.advance(2000)

        self.assertEqual(board.get_piece(Position(0, 2)), piece)
        self.assertEqual(arbiter.motions, [])

    def test_game_over_stops_resolving_further_due_motions_in_the_same_call(self):
        # Both motions are requested/scheduled before either resolves (as if
        # a second piece were clicked while the king-capturing move was
        # still mid-flight). Once the capture flips game_over, no further
        # motion - even one already due in this same batch - may complete.
        arbiter, board, rule_engine = make_arbiter(cols=3, rules={"R": allow_rule(), "K": allow_rule()})
        attacker = make_piece("w", "R", 0, 0)
        king = make_piece("b", "K", 0, 1)
        bystander = make_piece("w", "R", 2, 0)
        board.add_piece(attacker)
        board.add_piece(king)
        board.add_piece(bystander)

        capture = translate_motion(attacker, Position(0, 0), Position(0, 1), start_time=0, duration=1000, sequence=1)
        unrelated = translate_motion(bystander, Position(2, 0), Position(2, 1), start_time=0, duration=1000, sequence=2)
        arbiter.schedule(capture)
        arbiter.schedule(unrelated)

        arbiter.advance(1000)

        self.assertTrue(arbiter.game_over)
        self.assertEqual(board.get_piece(Position(0, 1)), attacker)  # capture went through
        self.assertIsNone(board.get_piece(Position(2, 1)))  # bystander's move did not
        self.assertIn(unrelated, arbiter.motions)  # left pending, never resolved


class TestResolveJumpMotion(unittest.TestCase):

    def test_jump_motion_only_idles_the_piece(self):
        arbiter, board, rule_engine = make_arbiter()
        piece = make_piece("w", "K", 1, 1)
        board.add_piece(piece)
        arbiter.schedule(jump_motion(piece, Position(1, 1), start_time=0, duration=1000))

        arbiter.advance(1000)

        self.assertEqual(piece.get_state(), STATE_IDLE)
        self.assertEqual(board.get_piece(Position(1, 1)), piece)


class TestResolveGhostMotion(unittest.TestCase):

    def test_motion_whose_piece_is_no_longer_at_its_origin_is_silently_dropped(self):
        # Simulates the piece having already been removed from the board by
        # some other resolution before this motion came due.
        arbiter, board, rule_engine = make_arbiter(rules={"R": allow_rule()})
        piece = make_piece("w", "R", 0, 0)
        board.add_piece(piece)
        motion = translate_motion(piece, Position(0, 0), Position(0, 1), start_time=0, duration=1000)
        arbiter.schedule(motion)
        board.remove_piece(Position(0, 0))  # piece vanishes from its origin

        arbiter.advance(1000)

        self.assertIsNone(board.get_piece(Position(0, 1)))
        self.assertNotIn(motion, arbiter.motions)
        # _resolve returns before reaching set_state("idle") for this branch.
        self.assertEqual(piece.get_state(), STATE_MOVING)


class TestResolveActiveEnemyJump(unittest.TestCase):

    def test_arriving_piece_is_removed_when_destination_has_an_active_enemy_jump(self):
        arbiter, board, rule_engine = make_arbiter(rules={"R": allow_rule()})
        mover = make_piece("w", "R", 0, 0)
        jumper = make_piece("b", "K", 0, 1)
        board.add_piece(mover)
        board.add_piece(jumper)
        # Same finish time: translate is tie-broken ahead of jump, so the
        # jump is still "active" (in self.motions) when translate resolves.
        arbiter.schedule(translate_motion(mover, Position(0, 0), Position(0, 1), start_time=0, duration=1000, sequence=1))
        arbiter.schedule(jump_motion(jumper, Position(0, 1), start_time=0, duration=1000, sequence=2))

        arbiter.advance(1000)

        # The mover vanishes entirely; the jumper never left its square on
        # the board (a jump motion doesn't move anything physically) and
        # stays put once it resolves.
        self.assertIsNone(board.get_piece(Position(0, 0)))
        self.assertEqual(board.get_piece(Position(0, 1)), jumper)
        self.assertEqual(mover.get_state(), STATE_IDLE)

    def test_same_color_jump_at_destination_does_not_trigger_removal(self):
        arbiter, board, rule_engine = make_arbiter(rules={"R": allow_rule()})
        mover = make_piece("w", "R", 0, 0)
        friendly_jumper = make_piece("w", "K", 0, 1)
        board.add_piece(mover)
        board.add_piece(friendly_jumper)
        arbiter.schedule(translate_motion(mover, Position(0, 0), Position(0, 1), start_time=0, duration=1000, sequence=1))
        arbiter.schedule(jump_motion(friendly_jumper, Position(0, 1), start_time=0, duration=1000, sequence=2))

        arbiter.advance(1000)

        # Same-color occupant at destination: falls through to the normal
        # same-color block instead, bouncing back to the leg's own source.
        self.assertEqual(board.get_piece(Position(0, 0)), mover)


class TestResolveRuleRecheck(unittest.TestCase):

    def test_unknown_piece_kind_lands_back_at_the_legs_own_source(self):
        arbiter, board, rule_engine = make_arbiter(rules={})  # no "R" entry
        piece = make_piece("w", "R", 0, 0)
        board.add_piece(piece)
        arbiter.schedule(translate_motion(piece, Position(0, 0), Position(0, 1), start_time=0, duration=1000))

        arbiter.advance(1000)

        self.assertEqual(board.get_piece(Position(0, 0)), piece)
        self.assertEqual(piece.get_state(), STATE_IDLE)

    def test_rule_rejecting_the_leg_lands_back_at_the_legs_own_source(self):
        deny_rule = Mock()
        deny_rule.is_legal.return_value = False
        arbiter, board, rule_engine = make_arbiter(rules={"R": deny_rule})
        piece = make_piece("w", "R", 0, 0)
        board.add_piece(piece)
        arbiter.schedule(translate_motion(piece, Position(0, 0), Position(0, 1), start_time=0, duration=1000))

        arbiter.advance(1000)

        self.assertEqual(board.get_piece(Position(0, 0)), piece)
        self.assertEqual(piece.get_state(), STATE_IDLE)

    def test_rule_is_consulted_with_the_legs_own_source_and_destination(self):
        rule = allow_rule()
        arbiter, board, rule_engine = make_arbiter(rules={"R": rule})
        piece = make_piece("w", "R", 0, 0)
        board.add_piece(piece)
        leg_source, leg_destination = Position(0, 0), Position(0, 1)
        arbiter.schedule(translate_motion(piece, leg_source, leg_destination, start_time=0, duration=1000))

        arbiter.advance(1000)

        rule.is_legal.assert_called_once_with(board, piece, leg_source, leg_destination)


class TestResolveOccupantHandling(unittest.TestCase):

    def test_same_color_occupant_at_destination_bounces_back_to_source(self):
        arbiter, board, rule_engine = make_arbiter(rules={"R": allow_rule()})
        mover = make_piece("w", "R", 0, 0)
        blocker = make_piece("w", "P", 0, 1)
        board.add_piece(mover)
        board.add_piece(blocker)
        arbiter.schedule(translate_motion(mover, Position(0, 0), Position(0, 1), start_time=0, duration=1000))

        arbiter.advance(1000)

        self.assertEqual(board.get_piece(Position(0, 0)), mover)
        self.assertEqual(board.get_piece(Position(0, 1)), blocker)
        self.assertEqual(mover.get_state(), STATE_IDLE)

    def test_enemy_occupant_is_captured_and_piece_lands_on_destination(self):
        arbiter, board, rule_engine = make_arbiter(rules={"R": allow_rule()})
        mover = make_piece("w", "R", 0, 0)
        enemy = make_piece("b", "P", 0, 1)
        board.add_piece(mover)
        board.add_piece(enemy)
        arbiter.schedule(translate_motion(mover, Position(0, 0), Position(0, 1), start_time=0, duration=1000))

        arbiter.advance(1000)

        self.assertEqual(board.get_piece(Position(0, 1)), mover)
        self.assertFalse(arbiter.game_over)

    def test_capturing_enemy_king_sets_game_over(self):
        arbiter, board, rule_engine = make_arbiter(rules={"R": allow_rule()})
        mover = make_piece("w", "R", 0, 0)
        enemy_king = make_piece("b", "K", 0, 1)
        board.add_piece(mover)
        board.add_piece(enemy_king)
        arbiter.schedule(translate_motion(mover, Position(0, 0), Position(0, 1), start_time=0, duration=1000))

        arbiter.advance(1000)

        self.assertTrue(arbiter.game_over)
        self.assertEqual(arbiter.winner, "w")

    def test_capturing_non_king_enemy_does_not_set_game_over(self):
        arbiter, board, rule_engine = make_arbiter(rules={"R": allow_rule()})
        mover = make_piece("w", "R", 0, 0)
        enemy = make_piece("b", "Q", 0, 1)
        board.add_piece(mover)
        board.add_piece(enemy)
        arbiter.schedule(translate_motion(mover, Position(0, 0), Position(0, 1), start_time=0, duration=1000))

        arbiter.advance(1000)

        self.assertFalse(arbiter.game_over)

    def test_capturing_an_in_flight_enemy_removes_its_pending_motion_too(self):
        arbiter, board, rule_engine = make_arbiter(cols=4, rules={"R": allow_rule()})
        mover = make_piece("w", "R", 0, 0)
        enemy = make_piece("b", "R", 0, 1)
        board.add_piece(mover)
        board.add_piece(enemy)
        enemy_motion = translate_motion(enemy, Position(0, 1), Position(0, 2), start_time=0, duration=1000, sequence=2)
        arbiter.schedule(translate_motion(mover, Position(0, 0), Position(0, 1), start_time=0, duration=1000, sequence=1))
        arbiter.schedule(enemy_motion)

        arbiter.advance(1000)

        self.assertEqual(board.get_piece(Position(0, 1)), mover)
        self.assertNotIn(enemy_motion, arbiter.motions)

    def test_capturing_in_flight_enemy_continues_remaining_route_instead_of_landing(self):
        arbiter, board, rule_engine = make_arbiter(cols=4, rules={"R": allow_rule()})
        mover = make_piece("w", "R", 0, 0)
        enemy = make_piece("b", "R", 0, 1)
        board.add_piece(mover)
        board.add_piece(enemy)
        enemy_motion = translate_motion(enemy, Position(0, 1), Position(0, 2), start_time=0, duration=1000, sequence=2)
        mover_motion = translate_motion(mover, Position(0, 0), Position(0, 1), start_time=0, duration=1000,
                                         sequence=1, remaining_route=[Position(0, 2)])
        arbiter.schedule(mover_motion)
        arbiter.schedule(enemy_motion)

        arbiter.advance(2000)

        self.assertEqual(board.get_piece(Position(0, 2)), mover)

    def test_empty_destination_continues_remaining_route(self):
        arbiter, board, rule_engine = make_arbiter(cols=4, rules={"R": allow_rule()})
        piece = make_piece("w", "R", 0, 0)
        board.add_piece(piece)
        motion = translate_motion(piece, Position(0, 0), Position(0, 1), start_time=0, duration=1000,
                                   remaining_route=[Position(0, 2)])
        arbiter.schedule(motion)

        arbiter.advance(1000)

        # Still mid-route: piece's tracked position updated but board grid
        # only reflects the move once the whole route lands.
        self.assertEqual(piece.get_position().get_col(), 1)
        self.assertEqual(len(arbiter.motions), 1)

    def test_empty_destination_with_no_remaining_route_lands(self):
        arbiter, board, rule_engine = make_arbiter(rules={"R": allow_rule()})
        piece = make_piece("w", "R", 0, 0)
        board.add_piece(piece)
        arbiter.schedule(translate_motion(piece, Position(0, 0), Position(0, 1), start_time=0, duration=1000))

        arbiter.advance(1000)

        self.assertEqual(board.get_piece(Position(0, 1)), piece)

    def test_occupant_matching_the_moving_piece_itself_is_treated_as_no_occupant(self):
        # Defensive branch: _occupant_at can only report a piece via a
        # translate motion still present in self.motions. advance() always
        # removes the motion under resolution before calling _resolve, so
        # under normal single-motion-per-piece use this can't self-match;
        # this test forces it by leaving a duplicate motion entry in place.
        arbiter, board, rule_engine = make_arbiter(rules={"R": allow_rule()})
        piece = make_piece("w", "R", 0, 0)
        board.add_piece(piece)
        motion = translate_motion(piece, Position(0, 0), Position(0, 1), start_time=0, duration=1000)
        duplicate = translate_motion(piece, Position(0, 0), Position(0, 1), start_time=0, duration=1000, sequence=99)
        # _occupant_at matches by the piece's *currently tracked* position,
        # not the motion's original source; it must equal the destination
        # for this piece to be found as its own "occupant".
        piece.set_position(Position(0, 1))
        arbiter.motions = [duplicate]

        arbiter._resolve(motion)

        self.assertEqual(board.get_piece(Position(0, 1)), piece)


class TestLandAndPromotion(unittest.TestCase):

    def test_non_pawn_piece_is_not_promoted_on_the_back_row(self):
        arbiter, board, rule_engine = make_arbiter(rows=3, rules={"R": allow_rule()})
        piece = make_piece("w", "R", 1, 0)
        board.add_piece(piece)
        arbiter.schedule(translate_motion(piece, Position(1, 0), Position(0, 0), start_time=0, duration=1000))

        arbiter.advance(1000)

        self.assertEqual(piece.get_kind(), "R")

    def test_white_pawn_promotes_on_row_zero(self):
        arbiter, board, rule_engine = make_arbiter(rows=3, rules={"P": allow_rule()})
        piece = make_piece("w", "P", 1, 0)
        board.add_piece(piece)
        arbiter.schedule(translate_motion(piece, Position(1, 0), Position(0, 0), start_time=0, duration=1000))

        arbiter.advance(1000)

        self.assertEqual(piece.get_kind(), "Q")

    def test_white_pawn_not_on_row_zero_is_not_promoted(self):
        arbiter, board, rule_engine = make_arbiter(rows=3, rules={"P": allow_rule()})
        piece = make_piece("w", "P", 2, 0)
        board.add_piece(piece)
        arbiter.schedule(translate_motion(piece, Position(2, 0), Position(1, 0), start_time=0, duration=1000))

        arbiter.advance(1000)

        self.assertEqual(piece.get_kind(), "P")

    def test_black_pawn_promotes_on_the_last_row_which_scales_with_board_size(self):
        arbiter, board, rule_engine = make_arbiter(rows=5, rules={"P": allow_rule()})
        piece = make_piece("b", "P", 3, 0)
        board.add_piece(piece)
        arbiter.schedule(translate_motion(piece, Position(3, 0), Position(4, 0), start_time=0, duration=1000))

        arbiter.advance(1000)

        self.assertEqual(piece.get_kind(), "Q")

    def test_black_pawn_not_on_last_row_is_not_promoted(self):
        arbiter, board, rule_engine = make_arbiter(rows=5, rules={"P": allow_rule()})
        piece = make_piece("b", "P", 2, 0)
        board.add_piece(piece)
        arbiter.schedule(translate_motion(piece, Position(2, 0), Position(3, 0), start_time=0, duration=1000))

        arbiter.advance(1000)

        self.assertEqual(piece.get_kind(), "P")

    def test_land_moves_piece_on_the_board_from_origin_to_the_landing_cell(self):
        arbiter, board, rule_engine = make_arbiter(rules={"R": allow_rule()})
        piece = make_piece("w", "R", 0, 0)
        board.add_piece(piece)
        motion = translate_motion(piece, Position(0, 0), Position(0, 2))

        arbiter._land(motion, Position(0, 2))

        self.assertIsNone(board.get_piece(Position(0, 0)))
        self.assertEqual(board.get_piece(Position(0, 2)), piece)


class TestCooldownScheduling(unittest.TestCase):

    def test_source_is_busy_right_after_a_move_lands(self):
        arbiter, board, rule_engine = make_arbiter(rules={"R": allow_rule()})
        piece = make_piece("w", "R", 0, 0)
        board.add_piece(piece)
        arbiter.schedule(translate_motion(piece, Position(0, 0), Position(0, 1), start_time=0, duration=1000))

        arbiter.advance(1000)

        self.assertTrue(arbiter.is_source_busy(Position(0, 1)))
        self.assertEqual(piece.get_rest_type(), REST_LONG)
        self.assertEqual(piece.get_rest_progress(), 0.0)

    def test_rest_progress_advances_as_the_move_cooldown_elapses(self):
        arbiter, board, rule_engine = make_arbiter(rules={"R": allow_rule()})
        piece = make_piece("w", "R", 0, 0)
        board.add_piece(piece)
        arbiter.schedule(translate_motion(piece, Position(0, 0), Position(0, 1), start_time=0, duration=1000))

        arbiter.advance(1000)  # move lands, cooldown starts
        arbiter.advance(1000 + MOVE_COOLDOWN_TIME // 2)

        self.assertAlmostEqual(piece.get_rest_progress(), 0.5)

    def test_source_frees_up_once_the_move_cooldown_elapses(self):
        arbiter, board, rule_engine = make_arbiter(rules={"R": allow_rule()})
        piece = make_piece("w", "R", 0, 0)
        board.add_piece(piece)
        arbiter.schedule(translate_motion(piece, Position(0, 0), Position(0, 1), start_time=0, duration=1000))

        arbiter.advance(1000 + MOVE_COOLDOWN_TIME)

        self.assertFalse(arbiter.is_source_busy(Position(0, 1)))
        self.assertEqual(piece.get_rest_type(), REST_NONE)
        self.assertEqual(piece.get_rest_progress(), 0.0)

    def test_source_is_busy_right_after_a_jump_resolves(self):
        arbiter, board, rule_engine = make_arbiter()
        piece = make_piece("w", "K", 1, 1)
        board.add_piece(piece)
        arbiter.schedule(jump_motion(piece, Position(1, 1), start_time=0, duration=1000))

        arbiter.advance(1000)

        self.assertTrue(arbiter.is_source_busy(Position(1, 1)))
        self.assertEqual(piece.get_rest_type(), REST_SHORT)

    def test_source_frees_up_once_the_jump_cooldown_elapses(self):
        arbiter, board, rule_engine = make_arbiter()
        piece = make_piece("w", "K", 1, 1)
        board.add_piece(piece)
        arbiter.schedule(jump_motion(piece, Position(1, 1), start_time=0, duration=1000))

        arbiter.advance(1000 + JUMP_COOLDOWN_TIME)

        self.assertFalse(arbiter.is_source_busy(Position(1, 1)))
        self.assertEqual(piece.get_rest_type(), REST_NONE)

    def test_bouncing_back_to_the_legs_own_source_still_starts_a_cooldown_there(self):
        deny_rule = Mock()
        deny_rule.is_legal.return_value = False
        arbiter, board, rule_engine = make_arbiter(rules={"R": deny_rule})
        piece = make_piece("w", "R", 0, 0)
        board.add_piece(piece)
        arbiter.schedule(translate_motion(piece, Position(0, 0), Position(0, 1), start_time=0, duration=1000))

        arbiter.advance(1000)

        self.assertTrue(arbiter.is_source_busy(Position(0, 0)))

    def test_no_cooldown_is_started_for_a_piece_captured_mid_flight(self):
        arbiter, board, rule_engine = make_arbiter(cols=4, rules={"R": allow_rule()})
        mover = make_piece("w", "R", 0, 0)
        enemy = make_piece("b", "R", 0, 1)
        board.add_piece(mover)
        board.add_piece(enemy)
        enemy_motion = translate_motion(enemy, Position(0, 1), Position(0, 2), start_time=0, duration=1000, sequence=2)
        arbiter.schedule(translate_motion(mover, Position(0, 0), Position(0, 1), start_time=0, duration=1000, sequence=1))
        arbiter.schedule(enemy_motion)

        arbiter.advance(1000)

        # Only the winning mover lands and starts a cooldown; the captured
        # enemy never reaches _land, so it gets none.
        self.assertEqual([c.piece for c in arbiter.cooldowns], [mover])


class TestOccupantAt(unittest.TestCase):

    def test_returns_in_flight_translate_piece_currently_at_position(self):
        arbiter, board, rule_engine = make_arbiter()
        piece = make_piece("w", "R", 0, 0)
        board.add_piece(piece)
        motion = translate_motion(piece, Position(0, 0), Position(0, 2))
        piece.set_position(Position(0, 1))  # mid-route tracked position
        arbiter.motions = [motion]

        occupant = arbiter._occupant_at(Position(0, 1))

        self.assertIs(occupant, piece)

    def test_ignores_jump_kind_motions(self):
        arbiter, board, rule_engine = make_arbiter()
        piece = make_piece("w", "K", 1, 1)
        board.add_piece(piece)
        arbiter.motions = [jump_motion(piece, Position(1, 1))]

        occupant = arbiter._occupant_at(Position(1, 1))

        # Falls through to the static board, which does have the piece.
        self.assertIs(occupant, piece)

    def test_falls_back_to_board_when_no_in_flight_motion_matches(self):
        arbiter, board, rule_engine = make_arbiter()
        piece = make_piece("w", "R", 0, 0)
        board.add_piece(piece)

        occupant = arbiter._occupant_at(Position(0, 0))

        self.assertIs(occupant, piece)

    def test_returns_none_for_a_truly_empty_square(self):
        arbiter, board, rule_engine = make_arbiter()
        self.assertIsNone(arbiter._occupant_at(Position(2, 2)))


class TestRemovePiece(unittest.TestCase):

    def test_removes_an_in_flight_piece_via_its_motion_origin(self):
        arbiter, board, rule_engine = make_arbiter()
        piece = make_piece("w", "R", 0, 0)
        board.add_piece(piece)
        motion = translate_motion(piece, Position(0, 0), Position(0, 1))
        arbiter.motions = [motion]

        removed_in_flight = arbiter._remove_piece(piece)

        self.assertTrue(removed_in_flight)
        self.assertIsNone(board.get_piece(Position(0, 0)))
        self.assertNotIn(motion, arbiter.motions)

    def test_removes_a_static_piece_via_its_own_current_position(self):
        arbiter, board, rule_engine = make_arbiter()
        piece = make_piece("w", "R", 1, 1)
        board.add_piece(piece)

        removed_in_flight = arbiter._remove_piece(piece)

        self.assertFalse(removed_in_flight)
        self.assertIsNone(board.get_piece(Position(1, 1)))

    def test_only_removes_the_matching_pieces_motion(self):
        # other_motion is placed first so the scan has to pass over a
        # non-matching entry before it reaches the matching one.
        arbiter, board, rule_engine = make_arbiter()
        target = make_piece("w", "R", 0, 0)
        other = make_piece("b", "R", 2, 2)
        board.add_piece(target)
        board.add_piece(other)
        target_motion = translate_motion(target, Position(0, 0), Position(0, 1))
        other_motion = translate_motion(other, Position(2, 2), Position(2, 1))
        arbiter.motions = [other_motion, target_motion]

        arbiter._remove_piece(target)

        self.assertNotIn(target_motion, arbiter.motions)
        self.assertIn(other_motion, arbiter.motions)


class TestActiveEnemyJumpAt(unittest.TestCase):

    def test_true_for_enemy_jump_motion_at_position(self):
        arbiter, board, rule_engine = make_arbiter()
        enemy = make_piece("b", "K", 1, 1)
        arbiter.motions = [jump_motion(enemy, Position(1, 1))]

        self.assertTrue(arbiter._active_enemy_jump_at(Position(1, 1), "w"))

    def test_false_for_same_color_jump_motion_at_position(self):
        arbiter, board, rule_engine = make_arbiter()
        friendly = make_piece("w", "K", 1, 1)
        arbiter.motions = [jump_motion(friendly, Position(1, 1))]

        self.assertFalse(arbiter._active_enemy_jump_at(Position(1, 1), "w"))

    def test_false_for_enemy_translate_motion_at_position(self):
        arbiter, board, rule_engine = make_arbiter()
        enemy = make_piece("b", "R", 1, 1)
        arbiter.motions = [translate_motion(enemy, Position(1, 0), Position(1, 1))]

        self.assertFalse(arbiter._active_enemy_jump_at(Position(1, 1), "w"))

    def test_false_when_no_motions_at_all(self):
        arbiter, board, rule_engine = make_arbiter()
        self.assertFalse(arbiter._active_enemy_jump_at(Position(1, 1), "w"))

    def test_false_for_enemy_jump_at_a_different_position(self):
        arbiter, board, rule_engine = make_arbiter()
        enemy = make_piece("b", "K", 1, 1)
        arbiter.motions = [jump_motion(enemy, Position(1, 1))]

        self.assertFalse(arbiter._active_enemy_jump_at(Position(9, 9), "w"))


if __name__ == "__main__":
    unittest.main()
