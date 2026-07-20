from controller.controller import Controller
from controller.board_mapper import BoardMapper
from engine.game_engine import GameEngine
from engine.real_time_arbiter import RealTimeArbiter
from rules.rule_engine import RuleEngine


def build_controller(board):
    rule_engine = RuleEngine()
    arbiter = RealTimeArbiter(board, rule_engine)
    game_engine = GameEngine(board, rule_engine, arbiter)
    return Controller(game_engine, BoardMapper())
