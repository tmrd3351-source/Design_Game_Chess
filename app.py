from setup.game_setup import GameSetup
from controller.controller import Controller
from controller.board_mapper import BoardMapper
from engine.game_engine import GameEngine
from engine.real_time_arbiter import RealTimeArbiter
from rendering.cli_renderer import CliRenderer
from rules.rule_engine import RuleEngine

# Imported lazily so the CLI path (run()) never requires opencv.
from setup.board_setup import GuiBoardSetup
from rendering.gui_renderer import GuiRenderer
from gui.game_window import GameWindow
        
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
        renderer = CliRenderer()
        for command in commands:
            state = controller.apply_command(command)
            if state is not None:
                renderer.render(state.board)

    def run_gui(self, board_setup=None):
        board = (board_setup or GuiBoardSetup()).load()
        if board is None:
            return

        controller = self._build_controller(board)
        GameWindow(controller, GuiRenderer()).run()

    def _build_controller(self, board):
        rule_engine = RuleEngine()
        arbiter = RealTimeArbiter(board, rule_engine)
        game_engine = GameEngine(board, rule_engine, arbiter)
        return Controller(game_engine, BoardMapper())
