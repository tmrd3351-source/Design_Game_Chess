class Piece:

    def __init__(self, piece_id, color, kind, position):
        self.id = piece_id
        self.color = color
        self.kind = kind
        self.position = position
        self.state = "idle"

    def get_position(self):
        return self.position

    def set_position(self, position):
        self.position = position

    def get_color(self):
        return self.color

    def get_kind(self):
        return self.kind

    def get_state(self):
        return self.state

    def set_state(self, state):
        self.state = state
