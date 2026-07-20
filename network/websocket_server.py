import asyncio

import websockets

from network.serialization import serialize, deserialize
from network.network_publisher import NetworkPublisher
from network.protocol import PlayCommand, GameStarted

TICK_INTERVAL_SECONDS = 0.1


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
    that same GameStarted to the earlier caller's own connection."""

    def __init__(self, connection_router, game_manager, session_ticker, host="localhost", port=8765):
        self.connection_router = connection_router
        self.game_manager = game_manager
        self.session_ticker = session_ticker
        self.host = host
        self.port = port
        self.ready = asyncio.Event()
        self._connections_by_room = {}
        self._connections_by_username = {}
        self._wired_rooms = set()

    async def start(self):
        async with websockets.serve(self._handle_connection, self.host, self.port) as server:
            self.port = server.sockets[0].getsockname()[1]
            self.ready.set()
            await self._tick_forever()

    async def _tick_forever(self):
        while True:
            await asyncio.sleep(TICK_INTERVAL_SECONDS)
            self.session_ticker.tick()

    async def _handle_connection(self, websocket):
        try:
            async for message in websocket:
                await self._handle_message(websocket, message)
        finally:
            self._forget_connection(websocket)

    async def _handle_message(self, websocket, message):
        command = deserialize(message)
        response = self.connection_router.handle(command)
        if isinstance(command, PlayCommand):
            self._connections_by_username[command.username] = websocket

        if response is None:
            return

        room_id = getattr(response, "room_id", None)
        if room_id is not None:
            self._track_connection(websocket, room_id)
            self._ensure_publisher(room_id)

        if isinstance(response, GameStarted):
            await self._notify_matched_opponent(command.username, response)

        await websocket.send(serialize(response))

    async def _notify_matched_opponent(self, matched_username, response):
        session = self.game_manager.join_session(response.room_id)
        if session is None:
            return
        for username in session.players.values():
            if username == matched_username:
                continue
            opponent_ws = self._connections_by_username.get(username)
            if opponent_ws is None:
                continue
            self._track_connection(opponent_ws, response.room_id)
            await self._safe_send(opponent_ws, serialize(response))

    def _track_connection(self, websocket, room_id):
        self._connections_by_room.setdefault(room_id, set()).add(websocket)

    def _ensure_publisher(self, room_id):
        if room_id in self._wired_rooms:
            return
        session = self.game_manager.join_session(room_id)
        if session is None:
            return
        self._wired_rooms.add(room_id)
        NetworkPublisher(session.events, sink=lambda response: self._broadcast(room_id, response))

    def _broadcast(self, room_id, response):
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
