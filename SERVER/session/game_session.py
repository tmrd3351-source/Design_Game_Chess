from SERVER.setup.board_setup import GuiBoardSetup
from SERVER.setup.controller_factory import build_controller
from SERVER.events.event_bus import EventBus
from SERVER.events.event_types import (
    PLAYER_JOINED, GAME_STARTED, MOVE_COMPLETED, GAME_ENDED,
    PLAYER_DISCONNECTED, PLAYER_RECONNECTED,
)
from SERVER.model.move_result import MoveResult

SPECTATOR = "spectator"


def _default_controller_factory():
    return build_controller(GuiBoardSetup().load())


class GameSession:
    """One running game/room: the two seated players, anyone just watching,
    and the Controller driving the game itself. join() assigns seats in join
    order - the first two names become white/black, everyone after that is
    a spectator.

    Owns its own EventBus instance - events from one room must never reach
    another room's subscribers."""

    def __init__(self, room_id, controller_factory=None):
        self.room_id = room_id
        
        self.controller = (controller_factory or _default_controller_factory)()
        self.events = EventBus()
        self.players = {}
        self.spectators = []
        self.pending_disconnects = set()  # usernames mid-reconnect-grace-period

    def join(self, name):
        existing_role = self.color_of(name)
        if existing_role is not None:
            self.mark_reconnected(name)
            return existing_role

        if "w" not in self.players:
            self.players["w"] = name
            role = "w"
        elif "b" not in self.players:
            self.players["b"] = name
            role = "b"
        else:
            self.spectators.append(name)
            role = SPECTATOR

        self.events.publish(PLAYER_JOINED, name=name, role=role)
        if role == "b":
            self.events.publish(GAME_STARTED, room_id=self.room_id)

        return role

    def color_of(self, username):
        """The seat ("w"/"b") `username` was assigned, or None if they were
        never seated (unknown, or joined only as a spectator)."""
        for color, seated_username in self.players.items():
            if seated_username == username:
                return color
        return None

    def mark_disconnected(self, username):
        """Starts a reconnect grace period for a seated player whose
        connection just dropped - a no-op for spectators/unknown names,
        since only seated players can forfeit by disappearing."""
        if self.color_of(username) is None:
            return
        self.pending_disconnects.add(username)
        self.events.publish(PLAYER_DISCONNECTED, room_id=self.room_id, name=username)

    def mark_reconnected(self, username):
        if username not in self.pending_disconnects:
            return
        self.pending_disconnects.discard(username)
        self.events.publish(PLAYER_RECONNECTED, room_id=self.room_id, name=username)

    def is_reconnectable(self, username):
        """True while `username` is disconnected but still within their
        grace period, and the game hasn't already ended for real."""
        return username in self.pending_disconnects and not self.controller.game_engine.arbiter.game_over

    def forfeit_by_disconnect(self, username):
        """Called once a disconnected player's grace period runs out with no
        reconnect - the other seated player wins by forfeit, same GAME_ENDED
        shape as a real win so rating updates and client rendering both
        already know what to do with it."""
        arbiter = self.controller.game_engine.arbiter
        if arbiter.game_over:
            return
        self.pending_disconnects.discard(username)
        winner = next((color for color, seated in self.players.items() if seated != username), None)
        arbiter.game_over = True
        arbiter.winner = winner
        self.events.publish(GAME_ENDED, room_id=self.room_id, winner=winner, players=self.players)

    def get_state(self):
        return self.controller.get_state()

    def request_move(self, username, source, destination):
        """Room/identity-level gate in front of Controller.handle_move: only
        checks that `username` is seated and owns the piece at `source`
        (and that `destination` is at least on the board) - actual move
        legality is entirely GameEngine/RuleEngine's call, never re-checked
        here."""
        color = self.color_of(username)
        if color is None or not self.controller.can_control_piece(color, source):
            return MoveResult.illegal("not_your_piece")
        if not self.controller.inside_board(destination):
            return MoveResult.illegal("out_of_bounds")
        return self.controller.handle_move(source, destination)

    def request_jump(self, username, position):
        color = self.color_of(username)
        if color is None or not self.controller.can_control_piece(color, position):
            return MoveResult.illegal("not_your_piece")
        return self.controller.handle_jump(position)

    def advance(self, elapsed_ms):
        """Drives real elapsed time into the underlying Controller/GameEngine
        and publishes MOVE_COMPLETED/GAME_ENDED based on what actually
        changed - the only place that inspects arbiter state, so callers
        (SessionTicker) never need to know it exists."""
        arbiter = self.controller.game_engine.arbiter
        pending_before = list(arbiter.motions)
        was_game_over = arbiter.game_over

        self.controller.handle_wait(elapsed_ms)

        state = self.controller.get_state()
        if any(motion not in state.motions for motion in pending_before):
            self.events.publish(MOVE_COMPLETED, room_id=self.room_id, state=state)

        if state.game_over and not was_game_over:
            self.events.publish(GAME_ENDED, room_id=self.room_id,
                                 winner=state.winner, players=self.players)
