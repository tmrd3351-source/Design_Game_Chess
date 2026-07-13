from config.constants import MOVE_TIME
from engine.route import compute_route
from model.motion import Motion
from model.move_result import MoveResult


class GameEngine:

    def __init__(self, board, rule_engine, arbiter):
        self.board = board
        self.rule_engine = rule_engine
        self.arbiter = arbiter
        self.time = 0
        self._sequence_counter = 0

    def inside_board(self, position):
        return self.board.inside_bounds(position)

    def can_select(self, position):
        piece = self.board.get_piece(position)
        return piece is not None and not self.arbiter.is_source_busy(position)

    def is_same_side(self, source, target):
        source_piece = self.board.get_piece(source)
        target_piece = self.board.get_piece(target)
        return target_piece is not None and target_piece.get_color() == source_piece.get_color()

    def _next_sequence(self):
        self._sequence_counter += 1
        return self._sequence_counter

    def request_move(self, source, destination):
        if self.arbiter.game_over:
            return MoveResult.illegal("game_over")

        if self.arbiter.is_source_busy(source):
            return MoveResult.illegal("motion_in_progress")

        result = self.rule_engine.check(self.board, source, destination)
        if not result.is_valid:
            return result

        piece = self.board.get_piece(source)
        route = compute_route(piece.get_kind(), source, destination)
        motion = Motion(piece, source, source, route[0], self.time, MOVE_TIME,
                         kind="translate", sequence=self._next_sequence(),
                         remaining_route=route[1:])
        self.arbiter.schedule(motion)
        return result

    def request_jump(self, position):
        if self.arbiter.game_over:
            return MoveResult.illegal("game_over")

        if self.arbiter.is_source_busy(position):
            return MoveResult.illegal("motion_in_progress")

        piece = self.board.get_piece(position)
        if piece is None:
            return MoveResult.illegal("illegal_move")

        motion = Motion(piece, position, position, position, self.time, MOVE_TIME,
                         kind="jump", sequence=self._next_sequence())
        self.arbiter.schedule(motion)
        return MoveResult.legal()

    def wait(self, ms):
        self.time += ms
        self.arbiter.advance(self.time)

    def resolve(self):
        self.arbiter.advance(self.time)
