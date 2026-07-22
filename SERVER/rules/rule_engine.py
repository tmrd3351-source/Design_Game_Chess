from SERVER.model.move_result import MoveResult
from SERVER.rules.piece_rules import KingRule, QueenRule, BishopRule, KnightRule, RookRule, PawnRule
#To receive a request for a move and decide whether it is legal according to the rules of the game.


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

        rule = self.rules.get(piece.get_kind())
        if rule is None or not rule.is_legal(board, piece, source, destination):
            return MoveResult.illegal("illegal_move")

        return MoveResult.legal()
