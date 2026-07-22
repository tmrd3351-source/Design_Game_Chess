CELL_SIZE = 100

# Duplicated from SERVER/config/constants.py: these are the exact string
# values the server puts into a GameStateUpdated snapshot's piece/motion
# state, which the client matches on to pick which sprite/animation to show.
# Keep both copies' values in sync if they ever change.
REST_NONE = "NONE"
REST_SHORT = "SHORT"
REST_LONG = "LONG"

STATE_IDLE = "idle"
STATE_MOVING = "moving"
STATE_JUMPING = "jumping"

MOTION_TRANSLATE = "translate"
