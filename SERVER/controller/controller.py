from SHARED.model.game_state import GameState


class Controller:

    def __init__(self, game_engine, board_mapper, command_handlers=None):
        self.game_engine = game_engine
        self.board_mapper = board_mapper
        self.selected = None
        self.command_handlers = command_handlers or {
            "print": self._handle_print,
            "wait": self._handle_wait,
            "click": self._handle_click,
            "jump": self._handle_jump,
        }

    def apply_command(self, command):
        tokens = command.split()
        if not tokens:
            return None

        handler = self.command_handlers.get(tokens[0])
        if handler is None:
            return None

        return handler(tokens)

    def get_state(self):
        return GameState(self.game_engine.board,
                          self.game_engine.arbiter.winner,
                          self.game_engine.arbiter.game_over,
                          self.game_engine.arbiter.motions,
                          self.game_engine.arbiter.move_log,
                          self.game_engine.arbiter.get_score())

    def _handle_print(self, _tokens):
        self.game_engine.resolve()
        return self.get_state()

    def _handle_wait(self, tokens):
        if len(tokens) == 2:
            self.handle_wait(int(tokens[1]))

    def _handle_click(self, tokens):
        if len(tokens) == 3:
            self.handle_click(int(tokens[1]), int(tokens[2]))

    def _handle_jump(self, tokens):
        if len(tokens) == 3:
            self.handle_jump(int(tokens[1]), int(tokens[2]))

    def handle_wait(self, ms):
        self.game_engine.wait(ms)

    def handle_move(self, source, destination):
        self.game_engine.request_move(source, destination)

    def handle_jump(self, x, y):
        position = self.board_mapper.to_position(x, y)
        self.handle_square_jump(position)

    def handle_square_jump(self, position):
        if not self.game_engine.inside_board(position):
            return

        self.game_engine.request_jump(position)

    def handle_click(self, x, y):
        position = self.board_mapper.to_position(x, y)
        self.handle_square_click(position)

    def handle_square_click(self, position):
        if not self.game_engine.inside_board(position):
            return

        if self.selected is None:
            if self.game_engine.can_select(position):
                self.selected = position
            return

        source = self.selected

        if self.game_engine.is_same_side(source, position):
            self.selected = position if self.game_engine.can_select(position) else None
            return

        self.game_engine.request_move(source, position)
        self.selected = None
