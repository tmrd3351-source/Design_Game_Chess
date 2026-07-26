from SERVER.events.event_types import MOVE_COMPLETED, GAME_STARTED, GAME_ENDED
from SHARED.network.protocol import GameStateUpdated, GameStarted


class NetworkPublisher:
    """The single place that turns a GameSession's domain events into
    protocol Responses. `broadcast` goes to every connection in the room
    (MOVE_COMPLETED, GAME_ENDED - everyone sees the same state); `unicast`
    goes to one seated player's own connection at a time (GAME_STARTED,
    since each player needs their own color, not a shared payload). Both
    default to printing so this still works with no transport at all."""

    def __init__(self, session, broadcast=None, unicast=None):
        self.session = session
        self.broadcast = broadcast if broadcast is not None else print
        self.unicast = unicast if unicast is not None else (lambda username, response: print(username, response))
        session.events.subscribe(MOVE_COMPLETED, self._on_move_completed)
        session.events.subscribe(GAME_STARTED, self._on_game_started)
        session.events.subscribe(GAME_ENDED, self._on_game_ended)

    def _on_move_completed(self, room_id, state):
        self.broadcast(GameStateUpdated(room_id, state))

    def _on_game_started(self, room_id):
        for username in self.session.players.values():
            self.unicast(username, GameStarted(room_id, self.session.color_of(username)))

    def _on_game_ended(self, room_id, winner, players):
        self.broadcast(GameStateUpdated(room_id, self.session.get_state()))
