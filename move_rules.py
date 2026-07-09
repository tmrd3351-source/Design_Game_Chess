from constants import EMPTY_CELL


def is_move_legal(board, r1, c1, r2, c2):
    if not board.inside_board(r1, c1) or not board.inside_board(r2, c2):
        return False

    if (r1, c1) == (r2, c2):
        return False

    piece_code = board.get_cell(r1, c1)
    if piece_code == EMPTY_CELL:
        return False

    destination = board.get_cell(r2, c2)
    color, piece_type = piece_code[0], piece_code[1]

    if destination != EMPTY_CELL and destination[0] == color:
        return False

    dr = abs(r2 - r1)
    dc = abs(c2 - c1)

    rule = RULES.get(piece_type)
    if rule is None:
        return False

    return rule(board, r1, c1, r2, c2, color, dr, dc)


def king_rule(board, r1, c1, r2, c2, color, dr, dc):
    return dr <= 1 and dc <= 1


def rook_rule(board, r1, c1, r2, c2, color, dr, dc):
    return (r1 == r2 or c1 == c2) and board.is_path_clear(r1, c1, r2, c2)


def bishop_rule(board, r1, c1, r2, c2, color, dr, dc):
    return dr == dc and board.is_path_clear(r1, c1, r2, c2)


def queen_rule(board, r1, c1, r2, c2, color, dr, dc):
    return (r1 == r2 or c1 == c2 or dr == dc) and board.is_path_clear(r1, c1, r2, c2)


def knight_rule(board, r1, c1, r2, c2, color, dr, dc):
    return (dr == 2 and dc == 1) or (dr == 1 and dc == 2)


def pawn_rule(board, r1, c1, r2, c2, color, dr, dc):
    direction = -1 if color == "w" else 1

    if c1 == c2 and (r2 - r1 == direction):
        return board.get_cell(r2, c2) == EMPTY_CELL

    if dr == 1 and dc == 1 and (r2 - r1 == direction):
        return board.get_cell(r2, c2) != EMPTY_CELL

    return False


RULES = {
    "K": king_rule,
    "R": rook_rule,
    "B": bishop_rule,
    "Q": queen_rule,
    "N": knight_rule,
    "P": pawn_rule,
}
