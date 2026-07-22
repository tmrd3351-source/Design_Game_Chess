from SERVER.controller.controller import Controller
from SHARED.controller.board_mapper import BoardMapper
from SERVER.engine.game_engine import GameEngine
from SERVER.engine.real_time_arbiter import RealTimeArbiter
from SERVER.rules.rule_engine import RuleEngine


def build_controller(board):
    rule_engine = RuleEngine()
    arbiter = RealTimeArbiter(board, rule_engine)
    game_engine = GameEngine(board, rule_engine, arbiter)
    return Controller(game_engine, BoardMapper())
