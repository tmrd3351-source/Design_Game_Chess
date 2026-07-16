class Cooldown:
    """A fixed rest period at a single square, started once a motion lands
    there. While active, that square counts as busy (see
    RealTimeArbiter.is_source_busy) even though no Motion occupies it."""

    def __init__(self, piece, position, start_time, duration):
        self.piece = piece
        self.position = position
        self.start_time = start_time
        self.duration = duration
        self.progress = 0.0

    def update(self, current_time):
        elapsed = current_time - self.start_time
        self.progress = max(0.0, min(1.0, elapsed / self.duration))

    def is_complete(self):
        return self.progress >= 1.0
