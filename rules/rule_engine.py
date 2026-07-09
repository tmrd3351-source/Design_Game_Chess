from model.move_result import MoveResult
from rules.legal_destination import LegalDestination
from rules.piece_rules import KingRule, QueenRule, BishopRule, KnightRule, RookRule, PawnRule


DEFAULT_RULES = {
    "K": KingRule(),
    "Q": QueenRule(),
    "B": BishopRule(),
    "N": KnightRule(),
    "R": RookRule(),
    "P": PawnRule(),
}


class RuleEngine:

    def __init__(self, rules=None):
        self.rules = rules or DEFAULT_RULES

    def check(self, board, source, destination):
        if not board.inside_bounds(source):
            return MoveResult.illegal("illegal_move")

        piece = board.get_piece(source)
        if piece is None:
            return MoveResult.illegal("illegal_move")

        if source.equals(destination):
            return MoveResult.illegal("illegal_move")

        if not LegalDestination.check(board, destination, piece.get_color()):
            return MoveResult.illegal("blocked")

        rule = self.rules.get(piece.get_kind())
        if rule is None or not rule.is_legal(board, source, destination):
            return MoveResult.illegal("illegal_move")

        return MoveResult.legal()
