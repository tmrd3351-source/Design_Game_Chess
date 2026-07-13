import unittest
from unittest.mock import Mock

from model.position import Position
from model.move_result import MoveResult
from rules.rule_engine import RuleEngine, DEFAULT_RULES
from rules.piece_rules import KingRule, QueenRule, BishopRule, KnightRule, RookRule, PawnRule


def make_board(inside_bounds=True, piece_at_source=None):
    board = Mock()
    board.inside_bounds.return_value = inside_bounds
    board.get_piece.return_value = piece_at_source
    return board


class TestRuleEngineConstruction(unittest.TestCase):

    def test_default_rules_is_used_when_none_provided(self):
        engine = RuleEngine()
        self.assertIs(engine.rules, DEFAULT_RULES)

    def test_default_rules_maps_every_piece_kind_to_its_own_rule_type(self):
        self.assertIsInstance(DEFAULT_RULES["K"], KingRule)
        self.assertIsInstance(DEFAULT_RULES["Q"], QueenRule)
        self.assertIsInstance(DEFAULT_RULES["B"], BishopRule)
        self.assertIsInstance(DEFAULT_RULES["N"], KnightRule)
        self.assertIsInstance(DEFAULT_RULES["R"], RookRule)
        self.assertIsInstance(DEFAULT_RULES["P"], PawnRule)

    def test_custom_rules_dict_is_used_when_provided(self):
        custom_rules = {"K": Mock()}
        engine = RuleEngine(rules=custom_rules)
        self.assertIs(engine.rules, custom_rules)

    def test_empty_custom_rules_dict_falls_back_to_default(self):
        # `rules or DEFAULT_RULES` treats {} as falsy, same quirk as
        # Controller's command_handlers default.
        engine = RuleEngine(rules={})
        self.assertIs(engine.rules, DEFAULT_RULES)


class TestRuleEngineCheck(unittest.TestCase):

    def test_source_out_of_bounds_is_illegal_without_consulting_any_rule(self):
        board = make_board(inside_bounds=False)
        rule = Mock()
        engine = RuleEngine(rules={"R": rule})

        result = engine.check(board, Position(-1, 0), Position(0, 0))

        self.assertFalse(result.is_valid)
        self.assertEqual(result.reason, "illegal_move")
        rule.is_legal.assert_not_called()

    def test_empty_source_square_is_illegal(self):
        board = make_board(inside_bounds=True, piece_at_source=None)
        rule = Mock()
        engine = RuleEngine(rules={"R": rule})

        result = engine.check(board, Position(0, 0), Position(0, 1))

        self.assertFalse(result.is_valid)
        self.assertEqual(result.reason, "illegal_move")
        rule.is_legal.assert_not_called()

    def test_source_equal_to_destination_is_illegal(self):
        piece = Mock()
        piece.get_kind.return_value = "R"
        board = make_board(inside_bounds=True, piece_at_source=piece)
        rule = Mock()
        engine = RuleEngine(rules={"R": rule})

        result = engine.check(board, Position(2, 2), Position(2, 2))

        self.assertFalse(result.is_valid)
        self.assertEqual(result.reason, "illegal_move")
        rule.is_legal.assert_not_called()

    def test_unknown_piece_kind_with_no_matching_rule_is_illegal(self):
        piece = Mock()
        piece.get_kind.return_value = "Z"
        board = make_board(inside_bounds=True, piece_at_source=piece)
        engine = RuleEngine(rules={"R": Mock()})

        result = engine.check(board, Position(0, 0), Position(0, 1))

        self.assertFalse(result.is_valid)
        self.assertEqual(result.reason, "illegal_move")

    def test_rule_returning_false_is_illegal(self):
        piece = Mock()
        piece.get_kind.return_value = "R"
        board = make_board(inside_bounds=True, piece_at_source=piece)
        rule = Mock()
        rule.is_legal.return_value = False
        engine = RuleEngine(rules={"R": rule})

        result = engine.check(board, Position(0, 0), Position(1, 1))

        self.assertFalse(result.is_valid)
        self.assertEqual(result.reason, "illegal_move")

    def test_rule_returning_true_is_legal(self):
        piece = Mock()
        piece.get_kind.return_value = "R"
        board = make_board(inside_bounds=True, piece_at_source=piece)
        rule = Mock()
        rule.is_legal.return_value = True
        engine = RuleEngine(rules={"R": rule})

        result = engine.check(board, Position(0, 0), Position(0, 5))

        self.assertTrue(result.is_valid)
        self.assertEqual(result.reason, "legal")

    def test_rule_is_invoked_with_board_piece_source_and_destination(self):
        piece = Mock()
        piece.get_kind.return_value = "Q"
        board = make_board(inside_bounds=True, piece_at_source=piece)
        rule = Mock()
        rule.is_legal.return_value = True
        engine = RuleEngine(rules={"Q": rule})
        source, destination = Position(1, 1), Position(4, 4)

        engine.check(board, source, destination)

        rule.is_legal.assert_called_once_with(board, piece, source, destination)

    def test_only_source_bounds_are_checked_not_destination(self):
        # check() never calls board.inside_bounds on the destination; a
        # shape-legal move to an off-board destination is still reported
        # as legal by this method.
        piece = Mock()
        piece.get_kind.return_value = "R"
        board = make_board(inside_bounds=True, piece_at_source=piece)
        rule = Mock()
        rule.is_legal.return_value = True
        engine = RuleEngine(rules={"R": rule})
        source = Position(0, 0)

        result = engine.check(board, source, Position(0, 999))

        self.assertTrue(result.is_valid)
        # Position has no __eq__, only .equals(); assert_called_once_with
        # needs the exact same instance to compare equal.
        board.inside_bounds.assert_called_once_with(source)


class TestRuleEngineIntegration(unittest.TestCase):
    """A couple of end-to-end sanity checks with the real default rules and
    a real Board/Piece, to confirm the wiring (not just the mocked contract)."""

    def test_legal_rook_move_on_real_board(self):
        from model.board import Board
        from model.piece import Piece

        board = Board(3, 3)
        piece = Piece(0, "w", "R", Position(0, 0))
        board.add_piece(piece)
        engine = RuleEngine()

        result = engine.check(board, Position(0, 0), Position(0, 2))

        self.assertTrue(result.is_valid)

    def test_illegal_bishop_move_on_real_board(self):
        from model.board import Board
        from model.piece import Piece

        board = Board(3, 3)
        piece = Piece(0, "w", "B", Position(0, 0))
        board.add_piece(piece)
        engine = RuleEngine()

        result = engine.check(board, Position(0, 0), Position(0, 2))

        self.assertFalse(result.is_valid)


if __name__ == "__main__":
    unittest.main()
