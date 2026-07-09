from config.constants import MOVE_TIME
from model.motion import Motion
from model.move_result import MoveResult


class GameEngine:

    def __init__(self, board, rule_engine, arbiter):
        self.board = board
        self.rule_engine = rule_engine
        self.arbiter = arbiter
        self.time = 0

    def inside_board(self, position):
        return self.board.inside_bounds(position)

    def get_piece(self, position):
        return self.board.get_piece(position)

    def is_position_busy(self, position):
        return self.arbiter.is_source_busy(position)

    def request_move(self, source, destination):
        if self.arbiter.game_over:
            return MoveResult.illegal("game_over")

        if self.arbiter.has_active_motions():
            return MoveResult.illegal("motion_in_progress")

        result = self.rule_engine.check(self.board, source, destination)
        if not result.is_valid:
            return result

        piece = self.board.get_piece(source)
        motion = Motion(piece, source, destination, self.time, MOVE_TIME)
        self.arbiter.schedule(motion)
        return result

    def wait(self, ms):
        self.time += ms
        self.arbiter.advance(self.time)

    def resolve(self):
        self.arbiter.advance(self.time)
