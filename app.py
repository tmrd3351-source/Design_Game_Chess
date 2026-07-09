from controller.parser import parse_input, validate, build_board
from controller.controller import Controller
from controller.board_mapper import BoardMapper
from engine.game_engine import GameEngine
from engine.real_time_arbiter import RealTimeArbiter
from renderer.renderer import Renderer
from rules.rule_engine import RuleEngine


class Application:
    """Composition root: wires the object graph and runs the command stream."""

    def run(self):
        tokens, commands = parse_input()
        error = validate(tokens)

        if error:
            print(error)
            return

        controller = self._build_controller(tokens)
        for command in commands:
            controller.apply_command(command)

    def _build_controller(self, tokens):
        board = build_board(tokens)
        rule_engine = RuleEngine()
        arbiter = RealTimeArbiter(board, rule_engine)
        game_engine = GameEngine(board, rule_engine, arbiter)
        return Controller(game_engine, BoardMapper(), Renderer())
