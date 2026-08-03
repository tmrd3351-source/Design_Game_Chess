from SERVER.engine.model.motion import Motion
from SERVER.engine.model.cooldown import Cooldown
from SERVER.config.constants import (
    MOVE_COOLDOWN_TIME, JUMP_COOLDOWN_TIME, REST_NONE, REST_SHORT, REST_LONG,
    STATE_IDLE, STATE_MOVING, STATE_JUMPING, MOTION_TRANSLATE, MOTION_JUMP, PIECE_VALUES,
)
#לנהל את כל מה שקורה כאשר הזמן מתקדם והתנועות מסתיימות

class RealTimeArbiter:

    def __init__(self, board, rule_engine):
        self.board = board
        self.rule_engine = rule_engine
        self.motions = []
        self.cooldowns = []
        self.game_over = False
        self.winner = None
        self.move_log = []
        # piece.id -> kinds captured so far along its still-in-flight route;
        # flushed into a move_log entry once the whole route lands.
        self._pending_captures = {}

    def schedule(self, motion):
        motion.piece.set_state(STATE_JUMPING if motion.kind == MOTION_JUMP else STATE_MOVING)
        self.motions.append(motion)

    def is_source_busy(self, position):
        return (any(motion.origin.equals(position) for motion in self.motions)
                or any(cooldown.position.equals(position) for cooldown in self.cooldowns))

    def advance(self, current_time):
        while True:
            due = [m for m in self.motions
                   if m.start_time + m.duration <= current_time]
            if not due:
                break

            due.sort(key=lambda m: (m.start_time + m.duration,
                                    m.kind == MOTION_JUMP, m.sequence))
            motion = due[0]
            self.motions.remove(motion)
            self._resolve(motion)
            if self.game_over:
                break

        for motion in self.motions:
            motion.update(current_time)

        still_active = []
        for cooldown in self.cooldowns:
            if cooldown.start_time + cooldown.duration > current_time:
                still_active.append(cooldown)
            else:
                cooldown.piece.set_rest_type(REST_NONE)
                cooldown.piece.set_rest_progress(0.0)
        self.cooldowns = still_active

        for cooldown in self.cooldowns:
            cooldown.update(current_time)
            cooldown.piece.set_rest_progress(cooldown.progress)

    def _start_cooldown(self, piece, position, start_time, duration, rest_type):
        piece.set_rest_type(rest_type)
        piece.set_rest_progress(0.0)
        self.cooldowns.append(Cooldown(piece, position, start_time, duration))

    def _resolve(self, motion):
        piece = motion.piece

        if motion.kind == MOTION_JUMP:
            piece.set_state(STATE_IDLE)
            self._start_cooldown(piece, motion.origin,
                                  motion.start_time + motion.duration, JUMP_COOLDOWN_TIME, REST_SHORT)
            self.move_log.append({
                "color": piece.get_color(), "kind": piece.get_kind(),
                "source": motion.origin, "destination": motion.origin, "captured": [],
            })
            return

        if self.board.get_piece(motion.origin) is not piece:
            return

        destination = motion.destination

        if self._active_enemy_jump_at(destination, piece.get_color()):
            self.board.remove_piece(motion.origin)
            piece.set_state(STATE_IDLE)
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
                self.winner = piece.get_color()
            self._pending_captures.setdefault(piece.id, []).append(occupant.get_kind())
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
            kind=MOTION_TRANSLATE, sequence=motion.sequence,
            remaining_route=motion.remaining_route[1:],
        ))

    def _land(self, motion, cell):
        self.board.move_piece(motion.origin, cell)
        piece = motion.piece
        color, kind_before_promotion = piece.get_color(), piece.get_kind()
        piece.set_state(STATE_IDLE)
        if piece.get_kind() == "P" and self._is_promotion_row(piece, cell):
            piece.set_kind("Q")
        self._start_cooldown(piece, cell, motion.start_time + motion.duration, MOVE_COOLDOWN_TIME, REST_LONG)

        captured = self._pending_captures.pop(piece.id, [])
        if not cell.equals(motion.origin):
            self.move_log.append({
                "color": color, "kind": kind_before_promotion,
                "source": motion.origin, "destination": cell, "captured": captured,
            })

    def get_score(self):
        score = {"w": 0, "b": 0}
        for entry in self.move_log:
            for captured_kind in entry["captured"]:
                score[entry["color"]] += PIECE_VALUES.get(captured_kind, 0)
        return score

    def _is_promotion_row(self, piece, cell):
        last_row = 0 if piece.get_color() == "w" else self.board.rows - 1
        return cell.get_row() == last_row

    def _occupant_at(self, position):
        for motion in self.motions:
            if motion.kind == MOTION_TRANSLATE and motion.piece.get_position().equals(position):
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
            m.kind == MOTION_JUMP and m.piece.get_color() != color and m.origin.equals(position)
            for m in self.motions
        )
