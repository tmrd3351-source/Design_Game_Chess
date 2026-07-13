from model.motion import Motion
#לנהל את כל מה שקורה כאשר הזמן מתקדם והתנועות מסתיימות

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
        return any(motion.origin.equals(position) 
                   for motion in self.motions)

    def advance(self, current_time):
        while True:
            due = [m for m in self.motions
                   if m.start_time + m.duration <= current_time]
            if not due:
                break

            due.sort(key=lambda m: (m.start_time + m.duration,
                                    m.kind == "jump", m.sequence))
            motion = due[0]
            self.motions.remove(motion)
            self._resolve(motion)

        for motion in self.motions:
            motion.update(current_time)

    def _resolve(self, motion):
        piece = motion.piece

        if motion.kind == "jump":
            piece.set_state("idle")
            return

        if self.board.get_piece(motion.origin) is not piece:
            return

        destination = motion.destination

        if self._active_enemy_jump_at(destination, piece.get_color()):
            self.board.remove_piece(motion.origin)
            piece.set_state("idle")
            return

        rule = self.rule_engine.rules.get(piece.get_kind())
        if rule is None or not rule.is_legal(self.board, piece
                                             , motion.source, destination):
            self._land(motion, motion.source)
            return

        occupant = self._occupant_at(destination)
        if occupant is piece:
            occupant = None

        if occupant is not None and occupant.get_color() == piece.get_color():
            self._land(motion, motion.source)
            return

        if occupant is not None:
            if occupant.get_kind() == "K":
                self.game_over = True
            occupant_was_in_flight = self._remove_piece(occupant)
            if occupant_was_in_flight and motion.remaining_route:
                self._continue_route(motion, destination)
                return
            self._land(motion, destination)
            return

        if motion.remaining_route:
            self._continue_route(motion, destination)
            return

        self._land(motion, destination)

    def _continue_route(self, motion, destination):
        piece = motion.piece
        piece.set_position(destination)
        next_destination = motion.remaining_route[0]
        self.motions.append(Motion(
            piece, motion.origin, destination, next_destination,
            motion.start_time + motion.duration, motion.duration,
            kind="translate", sequence=motion.sequence,
            remaining_route=motion.remaining_route[1:],
        ))

    def _land(self, motion, cell):
        self.board.move_piece(motion.origin, cell)
        piece = motion.piece
        piece.set_state("idle")
        if piece.get_kind() == "P" and self._is_promotion_row(piece, cell):
            piece.set_kind("Q")

    def _is_promotion_row(self, piece, cell):
        last_row = 0 if piece.get_color() == "w" else self.board.rows - 1
        return cell.get_row() == last_row

    def _occupant_at(self, position):
        for motion in self.motions:
            if motion.kind == "translate" and motion.piece.get_position().equals(position):
                return motion.piece
        return self.board.get_piece(position)

    def _remove_piece(self, piece):
        for motion in self.motions:
            if motion.piece is piece:
                self.board.remove_piece(motion.origin)
                self.motions = [m for m in self.motions if m.piece is not piece]
                return True
        self.board.remove_piece(piece.get_position())
        return False

    def _active_enemy_jump_at(self, position, color):
        return any(
            m.kind == "jump" and m.piece.get_color() != color and m.origin.equals(position)
            for m in self.motions
        )
