from SERVER.engine.model.position import Position


def _path_is_clear(board, source, destination):
    """True if every square strictly between source and destination
    (exclusive of both) is empty. Only meaningful for straight-line
    (horizontal/vertical/diagonal) moves; callers must ensure the shape
    is valid before relying on this."""
    dr = destination.get_row() - source.get_row()
    dc = destination.get_col() - source.get_col()
    step_r = (dr // abs(dr)) if dr else 0
    step_c = (dc // abs(dc)) if dc else 0

    row = source.get_row() + step_r
    col = source.get_col() + step_c
    while (row, col) != (destination.get_row(), destination.get_col()):
        if board.is_occupied(Position(row, col)):
            return False
        row += step_r
        col += step_c

    return True


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
        if not (same_row or same_col or dr == dc):
            return False
        return _path_is_clear(board, source, destination)


class BishopRule:

    def is_legal(self, board, piece, source, destination):
        dr = abs(destination.get_row() - source.get_row())
        dc = abs(destination.get_col() - source.get_col())
        if dr != dc:
            return False
        return _path_is_clear(board, source, destination)


class KnightRule:

    def is_legal(self, board, piece, source, destination):
        dr = abs(destination.get_row() - source.get_row())
        dc = abs(destination.get_col() - source.get_col())
        return (dr == 2 and dc == 1) or (dr == 1 and dc == 2)


class RookRule:

    def is_legal(self, board, piece, source, destination):
        same_row = source.get_row() == destination.get_row()
        same_col = source.get_col() == destination.get_col()
        if not (same_row or same_col):
            return False
        return _path_is_clear(board, source, destination)


class PawnRule:

    def is_legal(self, board, piece, source, destination):
        direction = -1 if piece.get_color() == "w" else 1

        dr = destination.get_row() - source.get_row()
        dc = destination.get_col() - source.get_col()

        if dc == 0 and dr == direction:
            return board.get_piece(destination) is None

        start_row = board.rows - 1 if piece.get_color() == "w" else 0
        if dc == 0 and dr == 2 * direction and source.get_row() == start_row:
            return board.get_piece(destination) is None and _path_is_clear(board, source, destination)

        if abs(dc) == 1 and dr == direction:
            occupant = board.get_piece(destination)
            return occupant is not None and occupant.get_color() != piece.get_color()

        return False
