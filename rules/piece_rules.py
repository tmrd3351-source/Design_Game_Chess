class KingRule:

    def is_legal(self, board, piece, source, destination):
        dr = abs(destination.get_row() - source.get_row())
        dc = abs(destination.get_col() - source.get_col())
        return dr <= 1 and dc <= 1


class QueenRule:

    def is_legal(self, board, piece, source, destination):
        same_row = source.get_row() == destination.get_row()
        same_col = source.get_col() == destination.get_col()
        dr = abs(destination.get_row() - source.get_row())
        dc = abs(destination.get_col() - source.get_col())
        return same_row or same_col or dr == dc


class BishopRule:

    def is_legal(self, board, piece, source, destination):
        dr = abs(destination.get_row() - source.get_row())
        dc = abs(destination.get_col() - source.get_col())
        return dr == dc


class KnightRule:

    def is_legal(self, board, piece, source, destination):
        dr = abs(destination.get_row() - source.get_row())
        dc = abs(destination.get_col() - source.get_col())
        return (dr == 2 and dc == 1) or (dr == 1 and dc == 2)


class RookRule:

    def is_legal(self, board, piece, source, destination):
        same_row = source.get_row() == destination.get_row()
        same_col = source.get_col() == destination.get_col()
        return same_row or same_col


class PawnRule:

    def is_legal(self, board, piece, source, destination):
        direction = -1 if piece.get_color() == "w" else 1

        dr = destination.get_row() - source.get_row()
        dc = destination.get_col() - source.get_col()

        if dc == 0 and dr == direction:
            return board.get_piece(destination) is None

        start_row = board.rows - 2 if piece.get_color() == "w" else 1
        if dc == 0 and dr == 2 * direction and source.get_row() == start_row:
            return board.get_piece(destination) is None

        if abs(dc) == 1 and dr == direction:
            occupant = board.get_piece(destination)
            return occupant is not None and occupant.get_color() != piece.get_color()

        return False
