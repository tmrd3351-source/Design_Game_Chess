class Motion:

    def __init__(self, piece, source, destination, start_time, duration):
        self.piece = piece
        self.source = source
        self.destination = destination
        self.start_time = start_time
        self.duration = duration
        self.progress = 0.0

    def update(self, current_time):
        elapsed = current_time - self.start_time
        self.progress = max(0.0, min(1.0, elapsed / self.duration))

    def is_complete(self):
        return self.progress >= 1.0
