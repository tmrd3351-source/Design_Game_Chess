import asyncio

import websockets

from SHARED.network.serialization import serialize, deserialize
from SERVER.network.network_publisher import NetworkPublisher
from SHARED.network.protocol import (
    PlayCommand, CreateRoomCommand, JoinRoomCommand, GameStarted, GameStateUpdated,
)

TICK_INTERVAL_SECONDS = 0.1
DISCONNECT_GRACE_SECONDS = 20


class WebSocketServer:
    """Real transport for ConnectionRouter. For each connection: deserialize
    an incoming message into a Command, route it through
    connection_router.handle(), serialize the Response straight back to that
    same connection. Also tracks which connections belong to which room, so
    a NetworkPublisher (one per session, wired the first time a connection
    is seen joining that room) can broadcast MOVE_COMPLETED/GAME_ENDED
    updates to every connection in the room - not just whoever moved.

    Also drives SessionTicker.tick() on a fixed interval, since motions only
    resolve once real time elapses, independent of any incoming message.

    A PlayCommand that finds no match yet only gets Waiting() as its direct
    reply - the caller who was already queued has no room to be tracked
    under, so when a *later* PlayCommand matches them, this also pushes
    that same GameStarted to the earlier caller's own connection.

    Also handles disconnects: whenever a seated player's connection drops,
    their session gets a `disconnect_grace_seconds` window to reconnect
    (via a plain JoinRoomCommand for the same room/username - GameSession.
    join() already treats that as a reconnect, not a fresh seat) before the
    other player wins by forfeit."""

    def __init__(self, connection_router, game_manager, session_ticker, host="localhost", port=8765,
                 disconnect_grace_seconds=DISCONNECT_GRACE_SECONDS):
        self.connection_router = connection_router
        self.game_manager = game_manager
        self.session_ticker = session_ticker
        self.host = host
        self.port = port
        self.disconnect_grace_seconds = disconnect_grace_seconds
        self.ready = asyncio.Event()
        self._connections_by_room = {}
        self._connections_by_username = {}
        self._seat_by_connection = {}  # websocket -> (room_id, username)
        self._wired_rooms = set()
        self._rooms_broadcast_this_tick = set()

    async def start(self):
        async with websockets.serve(self._handle_connection, self.host, self.port) as server:
            self.port = server.sockets[0].getsockname()[1]
            self.ready.set()
            await self._tick_forever()

    async def _tick_forever(self):
        while True:
            await asyncio.sleep(TICK_INTERVAL_SECONDS)
            # Reset per-tick so _broadcast_active_rooms (below) can tell
            # whether NetworkPublisher already pushed this room's state
            # during session_ticker.tick() (a motion landing always starts
            # a fresh cooldown, so without this a landing gets broadcast
            # twice in the same tick: once from MOVE_COMPLETED, once from
            # the "still has an active cooldown" check right after).
            self._rooms_broadcast_this_tick = set()
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
        # arbiter itself ticks at.
        for room_id in list(self._connections_by_room.keys()):
            if room_id in self._rooms_broadcast_this_tick:
                continue
            session = self.game_manager.get_session(room_id)
            if session is None:
                continue
            arbiter = session.controller.game_engine.arbiter
            if not arbiter.motions and not arbiter.cooldowns:
                continue
            self._broadcast(room_id, GameStateUpdated(room_id, session.controller.get_state()))

    async def _handle_connection(self, websocket):
        try:
            async for message in websocket:
                await self._handle_message(websocket, message)
        except websockets.ConnectionClosed:
            # The peer disappeared without a clean close (window closed,
            # process killed, network drop) - expected and already handled
            # by _forget_connection below, not worth logging as an error.
            pass
        finally:
            self._forget_connection(websocket)

    async def _handle_message(self, websocket, message):
        command = deserialize(message)

        if isinstance(command, JoinRoomCommand):
            # GAME_STARTED can fire from inside session.join() during
            # handle() below, the moment this join fills the second seat -
            # unlike a PlayCommand match (whose room doesn't exist until
            # Matchmaker.find_match() creates it), this room_id is already
            # known, so the publisher must be wired before that happens,
            # not after.
            self._ensure_publisher(command.room_id)

        response = self.connection_router.handle(command)
        if isinstance(command, (PlayCommand, CreateRoomCommand, JoinRoomCommand)):
            self._connections_by_username[command.username] = websocket

        if response is None:
            return

        room_id = getattr(response, "room_id", None)
        if room_id is not None:
            self._track_connection(websocket, room_id)
            self._ensure_publisher(room_id)

        color = getattr(response, "color", None)
        if color is not None and room_id is not None:
            self._seat_by_connection[websocket] = (room_id, command.username)

        if isinstance(response, GameStarted):
            # A PlayCommand match: the room (and its publisher) didn't exist
            # before this call, so GAME_STARTED's own unicast never reached
            # the already-waiting opponent - push it to them directly instead.
            await self._notify_matched_opponent(command.username, response)

        await websocket.send(serialize(response))

    async def _notify_matched_opponent(self, matched_username, response):
        session = self.game_manager.get_session(response.room_id)
        if session is None:
            return
        for username in session.players.values():
            if username == matched_username:
                continue
            opponent_ws = self._connections_by_username.get(username)
            if opponent_ws is None:
                continue
            self._track_connection(opponent_ws, response.room_id)
            self._seat_by_connection[opponent_ws] = (response.room_id, username)
            # Not a resend of `response` - that one was built with the
            # matched caller's own color, which would be wrong here.
            opponent_response = GameStarted(response.room_id, session.color_of(username))
            await self._safe_send(opponent_ws, serialize(opponent_response))

    def _track_connection(self, websocket, room_id):
        self._connections_by_room.setdefault(room_id, set()).add(websocket)

    def _ensure_publisher(self, room_id):
        if room_id in self._wired_rooms:
            return
        session = self.game_manager.get_session(room_id)
        if session is None:
            return
        self._wired_rooms.add(room_id)
        NetworkPublisher(
            session,
            broadcast=lambda response: self._broadcast(room_id, response),
            unicast=self._send_to_username,
        )

    def _send_to_username(self, username, response):
        websocket = self._connections_by_username.get(username)
        if websocket is None:
            return
        asyncio.create_task(self._safe_send(websocket, serialize(response)))

    def _broadcast(self, room_id, response):
        if room_id in self._rooms_broadcast_this_tick:
            return

        self._rooms_broadcast_this_tick.add(room_id)
        message = serialize(response)
        for websocket in list(self._connections_by_room.get(room_id, ())):
            asyncio.create_task(self._safe_send(websocket, message))

    async def _safe_send(self, websocket, message):
        try:
            await websocket.send(message)
        except websockets.ConnectionClosed:
            pass

    def _forget_connection(self, websocket):
        for connections in self._connections_by_room.values():
            connections.discard(websocket)

        seat = self._seat_by_connection.pop(websocket, None)
        if seat is None:
            return
        room_id, username = seat
        session = self.game_manager.get_session(room_id)
        if session is None or session.controller.game_engine.arbiter.game_over:
            return
        session.mark_disconnected(username)
        asyncio.create_task(self._forfeit_after_grace_period(room_id, username))

    async def _forfeit_after_grace_period(self, room_id, username):
        await asyncio.sleep(self.disconnect_grace_seconds)
        session = self.game_manager.get_session(room_id)
        if session is None or not session.is_reconnectable(username):
            return  # reconnected in time, or the game already ended
        # forfeit_by_disconnect() publishes GAME_ENDED, which NetworkPublisher
        # (already wired for this room since it was created/joined earlier)
        # turns into the broadcast itself - no need to build one here too.
        session.forfeit_by_disconnect(username)
