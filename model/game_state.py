class GameState:

    def __init__(self, board, winner, game_over, motions=None):
        self.board = board
        self.winner = winner
        self.game_over = game_over
        self.motions = motions or []

    def to_dict(self):
        return {
            "board": self.board.to_dict(),
            "winner": self.winner,
            "game_over": self.game_over,
            "motions": [motion.to_dict() for motion in self.motions],
        }
