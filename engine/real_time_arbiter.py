class RealTimeArbiter:

    def __init__(self, board, rule_engine):
        self.board = board
        self.rule_engine = rule_engine
        self.motions = []
        self.game_over = False

    def schedule(self, motion):
        motion.piece.set_state("moving")
        self.motions.append(motion)

    def is_source_busy(self, position):
        return any(motion.source.equals(position) for motion in self.motions)

    def has_active_motions(self):
        return bool(self.motions)

    def advance(self, current_time):
        still_active = []
        for motion in self.motions:
            motion.update(current_time)
            if motion.is_complete():
                self._resolve(motion)
            else:
                still_active.append(motion)
        self.motions = still_active

    def _resolve(self, motion):
        piece = motion.piece
        piece.set_state("idle")

        if self.board.get_piece(motion.source) is not piece:
            return

        if not self.rule_engine.check(self.board, motion.source, motion.destination).is_valid:
            return

        target = self.board.get_piece(motion.destination)
        self.board.move_piece(motion.source, motion.destination)

        if target is not None and target.get_kind() == "K":
            self.game_over = True
