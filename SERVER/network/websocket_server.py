import asyncio

import websockets

from SHARED.network.serialization import serialize, deserialize
from SHARED.network.protocol import GameStateUpdated

TICK_INTERVAL_SECONDS = 0.1
DISCONNECT_GRACE_SECONDS = 20


class WebSocketServer:
    """Real transport for ConnectionRouter, and nothing more: for each
    connection, deserialize an incoming message into a Command and hand it
    straight to connection_router.handle() - no Response is ever built or
    sent from here. `handle()` itself produces no return value; instead
    ConnectionRouter (and, via it, NetworkPublisher) calls back into this
    class's own unicast()/broadcast() to actually deliver replies, which is
    why `router.publisher = self` is wired below.

    Also drives SessionTicker.tick() on a fixed interval, since motions only
    resolve once real time elapses, independent of any incoming message.

    Also handles disconnects: whenever a seated player's connection drops,
    their session gets a `disconnect_grace_seconds` window to reconnect
    (via a plain JoinRoomCommand for the same room/username - GameSession.
    join() already treats that as a reconnect, not a fresh seat) before the
    other player wins by forfeit."""

    def __init__(self, connection_router, game_manager, session_ticker, host="localhost", port=8765,
                 disconnect_grace_seconds=DISCONNECT_GRACE_SECONDS):
        self.connection_router = connection_router
        self.connection_router.publisher = self
        self.game_manager = game_manager
        self.session_ticker = session_ticker
        self.host = host
        self.port = port
        self.disconnect_grace_seconds = disconnect_grace_seconds
        self.ready = asyncio.Event()
        self._connections_by_username = {}
        self._username_by_connection = {}  # websocket -> username, for disconnect lookup
        self._last_broadcast_message = {}  # room_id -> last serialized message sent

    async def start(self):
        async with websockets.serve(self._handle_connection, self.host, self.port) as server:
            self.port = server.sockets[0].getsockname()[1]
            self.ready.set()
            await self._tick_forever()

    async def _tick_forever(self):
        while True:
            await asyncio.sleep(TICK_INTERVAL_SECONDS)
            self.session_ticker.tick()
            self._broadcast_active_rooms()

    def _broadcast_active_rooms(self):
        # NetworkPublisher only broadcasts on MOVE_COMPLETED/GAME_ENDED (a
        # motion landing or the game ending) - without this, a client sees
        # one snapshot when a move/jump is scheduled and the next only once
        # it lands, so anything that should animate continuously in between
        # (the sliding piece, the cooldown bar draining) would sit frozen.
        # Broadcasting every tick while a room has something actually in
        # flight keeps clients updated at the same ~100ms granularity the
        # arbiter itself ticks at. broadcast() itself dedupes against
        # whatever NetworkPublisher may have just sent this same tick, so
        # nothing here needs to track "did we already touch this room".
        for room_id, session in list(self.game_manager.sessions.items()):
            arbiter = session.controller.game_engine.arbiter
            if not arbiter.motions and not arbiter.cooldowns:
                continue
            self.broadcast(room_id, GameStateUpdated(room_id, session.controller.get_state()))

    async def _handle_connection(self, websocket):
        try:
            async for message in websocket:
                self._handle_message(websocket, message)
        except websockets.ConnectionClosed:
            # The peer disappeared without a clean close (window closed,
            # process killed, network drop) - expected and already handled
            # by _forget_connection below, not worth logging as an error.
            pass
        finally:
            self._forget_connection(websocket)

    def _handle_message(self, websocket, message):
        command = deserialize(message)

        username = getattr(command, "username", None)
        if username is not None:
            self._connections_by_username[username] = websocket
            self._username_by_connection[websocket] = username

        self.connection_router.handle(command)

    def unicast(self, username, response):
        websocket = self._connections_by_username.get(username)
        if websocket is None:
            return
        asyncio.create_task(self._safe_send(websocket, serialize(response)))

    def broadcast(self, room_id, response):
        # Dedup by actual content, not "already broadcast this tick" - a
        # disconnect-forfeit's GAME_ENDED fires from its own independent
        # asyncio timer, not the tick loop, so it can land in the same
        # ~100ms window as an unrelated broadcast for the same room. Content
        # comparison guarantees a message carrying genuinely new information
        # (game_over flipping to True, say) is never the one that gets
        # skipped - only a byte-identical repeat ever is.
        message = serialize(response)
        if self._last_broadcast_message.get(room_id) == message:
            return
        self._last_broadcast_message[room_id] = message

        session = self.game_manager.get_session(room_id)
        if session is None:
            return
        for username in list(session.players.values()) + list(session.spectators):
            websocket = self._connections_by_username.get(username)
            if websocket is None:
                continue
            asyncio.create_task(self._safe_send(websocket, message))

    async def _safe_send(self, websocket, message):
        try:
            await websocket.send(message)
        except websockets.ConnectionClosed:
            pass

    def _forget_connection(self, websocket):
        username = self._username_by_connection.pop(websocket, None)
        if username is None:
            return

        session = self._find_seated_session(username)
        if session is None or session.controller.game_engine.arbiter.game_over:
            return
        session.mark_disconnected(username)
        asyncio.create_task(self._forfeit_after_grace_period(session.room_id, username))

    def _find_seated_session(self, username):
        for session in self.game_manager.sessions.values():
            if session.color_of(username) is not None:
                return session
        return None

    async def _forfeit_after_grace_period(self, room_id, username):
        await asyncio.sleep(self.disconnect_grace_seconds)
        session = self.game_manager.get_session(room_id)
        if session is None or not session.is_reconnectable(username):
            return  # reconnected in time, or the game already ended
        # forfeit_by_disconnect() publishes GAME_ENDED, which NetworkPublisher
        # (already wired for this room since it was created/joined earlier)
        # turns into the broadcast itself - no need to build one here too.
        session.forfeit_by_disconnect(username)
