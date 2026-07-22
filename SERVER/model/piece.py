from SERVER.config.constants import REST_NONE, STATE_IDLE


class Piece:

    def __init__(self, piece_id, color, kind, position):
        self.id = piece_id
        self.color = color
        self.kind = kind
        self.position = position
        self.state = STATE_IDLE
        self.rest_type = REST_NONE
        self.rest_progress = 0.0

    def get_position(self):
        return self.position

    def set_position(self, position):
        self.position = position

    def get_color(self):
        return self.color

    def get_kind(self):
        return self.kind

    def set_kind(self, kind):
        self.kind = kind

    def get_state(self):
        return self.state

    def set_state(self, state):
        self.state = state

    def get_rest_type(self):
        return self.rest_type

    def set_rest_type(self, rest_type):
        self.rest_type = rest_type

    def get_rest_progress(self):
        return self.rest_progress

    def set_rest_progress(self, rest_progress):
        self.rest_progress = rest_progress

    def to_dict(self):
        return {
            "id": self.id,
            "color": self.color,
            "kind": self.kind,
            "position": self.position.to_dict(),
            "state": self.state,
            "rest_type": self.rest_type,
            "rest_progress": self.rest_progress,
        }
