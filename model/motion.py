class Motion:
    """A single-square leg of a (possibly multi-square) commanded move.

    `origin` is the cell where the board still shows the piece for as long as
    the overall route is mid-flight (board is only updated when the chain of
    legs terminates); `source`/`destination` are this leg's own from/to cell.
    """

    def __init__(self, piece, origin, source, destination, start_time, duration,
                 kind="translate", sequence=0, remaining_route=None):
        self.piece = piece
        self.origin = origin
        self.source = source
        self.destination = destination
        self.start_time = start_time
        self.duration = duration
        self.kind = kind
        self.sequence = sequence
        self.remaining_route = remaining_route or []
        self.progress = 0.0

    def update(self, current_time):
        elapsed = current_time - self.start_time
        self.progress = max(0.0, min(1.0, elapsed / self.duration))

    def is_complete(self):
        return self.progress >= 1.0
