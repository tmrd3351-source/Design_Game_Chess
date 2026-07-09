from constants import VALID_TOKENS


def validate(board):
    if board is None or board.rows == 0:
        return None

    width = board.cols
    for r in range(board.rows):
        row = board.get_row(r)
        if len(row) != width:
            return "ERROR ROW_WIDTH_MISMATCH"

        for token in row:
            if token not in VALID_TOKENS:
                return "ERROR UNKNOWN_TOKEN"

    return None