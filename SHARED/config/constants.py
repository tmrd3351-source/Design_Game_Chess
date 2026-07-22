EMPTY_CELL = "."
VALID_TOKENS = {
    EMPTY_CELL,
    "wK", "wQ", "wR", "wB", "wN", "wP",
    "bK", "bQ", "bR", "bB", "bN", "bP"
}

CELL_SIZE = 100
MOVE_TIME = 1000
MOVE_COOLDOWN_TIME = 1000
JUMP_COOLDOWN_TIME = 500

BOARD_HEADER = "Board:"
COMMANDS_HEADER = "Commands:"

REST_NONE = "NONE"
REST_SHORT = "SHORT"
REST_LONG = "LONG"

STATE_IDLE = "idle"
STATE_MOVING = "moving"
STATE_JUMPING = "jumping"

MOTION_TRANSLATE = "translate"
MOTION_JUMP = "jump"

PIECE_VALUES = {"P": 1, "N": 3, "B": 3, "R": 5, "Q": 9, "K": 0}
