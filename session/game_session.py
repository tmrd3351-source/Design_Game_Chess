from setup.board_setup import GuiBoardSetup
from setup.controller_factory import build_controller
from events.event_bus import EventBus
from events.event_types import PLAYER_JOINED, GAME_STARTED, MOVE_COMPLETED, GAME_ENDED

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

    def join(self, name):
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
