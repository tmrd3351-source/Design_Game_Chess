from SERVER.events.event_types import MOVE_COMPLETED
from SHARED.network.protocol import GameStateUpdated


class NetworkPublisher:
    """Subscribes to a GameSession's own EventBus and turns domain events
    into protocol Responses. `sink` is where a Response goes once built -
    defaults to `print` so this works with no transport at all; a real
    WebSocket layer later just passes a sink that serializes and sends it
    to every connection in this session instead."""

    def __init__(self, events, sink=None):
        events.subscribe(MOVE_COMPLETED, self._on_move_completed)
        self.sink = sink if sink is not None else print

    def _on_move_completed(self, room_id, state):
        self.sink(GameStateUpdated(room_id, state))
