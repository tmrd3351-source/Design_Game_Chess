from model.position import Position


def path_clear(board, source, destination):
    dr = destination.get_row() - source.get_row()
    dc = destination.get_col() - source.get_col()

    step_r = (dr // abs(dr)) if dr != 0 else 0
    step_c = (dc // abs(dc)) if dc != 0 else 0

    row = source.get_row() + step_r
    col = source.get_col() + step_c

    while (row, col) != (destination.get_row(), destination.get_col()):
        if board.get_piece(Position(row, col)) is not None:
            return False
        row += step_r
        col += step_c

    return True
