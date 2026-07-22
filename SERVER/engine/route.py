from SERVER.model.position import Position

SINGLE_STEP_KINDS = {"K", "N"}


def compute_route(piece_kind, source, destination):
    if piece_kind in SINGLE_STEP_KINDS:
        return [destination]

    dr = destination.get_row() - source.get_row()
    dc = destination.get_col() - source.get_col()
    step_r = (dr // abs(dr)) if dr else 0
    step_c = (dc // abs(dc)) if dc else 0

    row = source.get_row() + step_r
    col = source.get_col() + step_c

    route = []
    while (row, col) != (destination.get_row(), destination.get_col()):
        route.append(Position(row, col))
        row += step_r
        col += step_c

    route.append(destination)
    return route
