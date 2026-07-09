class LegalDestination:

    @staticmethod
    def check(board, position, color):
        if not board.inside_bounds(position):
            return False

        occupant = board.get_piece(position)
        return occupant is None or occupant.get_color() != color
