class LegalDestination:
    # Checks if a destination is legal for a piece of a given color.
    @staticmethod
    def check(board, position, color):
        if not board.inside_bounds(position):
            return False

        occupant = board.get_piece(position)
        return occupant is None or occupant.get_color() != color
