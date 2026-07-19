class GameState:

    def __init__(self, board, winner, game_over, motions=None):
        self.board = board
        self.winner = winner
        self.game_over = game_over
        self.motions = motions or []
