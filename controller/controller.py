class Controller:

    def __init__(self, game_engine, board_mapper, renderer, command_handlers=None):
        self.game_engine = game_engine
        self.board_mapper = board_mapper
        self.renderer = renderer
        self.selected = None
        self.command_handlers = command_handlers or {
            "print": self._handle_print,
            "wait": self._handle_wait,
            "click": self._handle_click,
        }

    def apply_command(self, command):
        tokens = command.split()
        if not tokens:
            return

        handler = self.command_handlers.get(tokens[0])
        if handler is None:
            return

        handler(tokens)

    def _handle_print(self, _tokens):
        self.game_engine.resolve()
        self.renderer.render(self.game_engine.board)

    def _handle_wait(self, tokens):
        if len(tokens) == 2:
            self.game_engine.wait(int(tokens[1]))

    def _handle_click(self, tokens):
        if len(tokens) == 3:
            self.handle_click(int(tokens[1]), int(tokens[2]))

    def handle_click(self, x, y):
        position = self.board_mapper.to_position(x, y)

        if not self.game_engine.inside_board(position):
            return

        piece = self.game_engine.get_piece(position)

        if self.selected is None:
            if piece is not None and not self.game_engine.is_position_busy(position):
                self.selected = position
            return

        source = self.selected
        source_piece = self.game_engine.get_piece(source)

        if piece is not None and piece.get_color() == source_piece.get_color():
            self.selected = None if self.game_engine.is_position_busy(position) else position
            return

        self.game_engine.request_move(source, position)
        self.selected = None
