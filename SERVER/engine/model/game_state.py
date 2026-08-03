class GameState:

    def __init__(self, board, winner, game_over, motions=None, move_log=None, score=None):
        self.board = board
        self.winner = winner
        self.game_over = game_over
        self.motions = motions or []
        self.move_log = move_log or []
        self.score = score if score is not None else {"w": 0, "b": 0}

    def to_dict(self):
        return {
            "board": self.board.to_dict(),
            "winner": self.winner,
            "game_over": self.game_over,
            "motions": [motion.to_dict() for motion in self.motions],
            "move_log": [
                {
                    "color": entry["color"],
                    "kind": entry["kind"],
                    "source": entry["source"].to_dict(),
                    "destination": entry["destination"].to_dict(),
                    "captured": entry["captured"],
                }
                for entry in self.move_log
            ],
            "score": self.score,
        }
