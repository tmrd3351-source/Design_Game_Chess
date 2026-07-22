from SERVER.model.game_state import GameState


class Controller:

    def __init__(self, game_engine):
        self.game_engine = game_engine

    def get_state(self):
        return GameState(self.game_engine.board,
                          self.game_engine.arbiter.winner,
                          self.game_engine.arbiter.game_over,
                          self.game_engine.arbiter.motions,
                          self.game_engine.arbiter.move_log,
                          self.game_engine.arbiter.get_score())

    def handle_wait(self, ms):
        self.game_engine.wait(ms)

    def handle_move(self, source, destination):
        self.game_engine.request_move(source, destination)
