from controller.game_setup import GameSetup
from controller.controller import Controller
from controller.board_mapper import BoardMapper
from engine.game_engine import GameEngine
from engine.real_time_arbiter import RealTimeArbiter
from renderer.renderer import Renderer
from rules.rule_engine import RuleEngine


class Application:
    """Composition root: wires the object graph and runs the command stream."""

    def __init__(self, game_setup=None):
        self.game_setup = game_setup or GameSetup()

    def run(self):
        result = self.game_setup.load()
        if result is None:
            return

        board, commands = result
        controller = self._build_controller(board)
        for command in commands:
            controller.apply_command(command)

    def _build_controller(self, board):
        rule_engine = RuleEngine()
        arbiter = RealTimeArbiter(board, rule_engine)
        game_engine = GameEngine(board, rule_engine, arbiter)
        return Controller(game_engine, BoardMapper(), Renderer())
