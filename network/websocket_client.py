import websockets

from network.serialization import serialize, deserialize


class WebSocketClient:
    """Real transport for sending Commands to a WebSocketServer and
    receiving Responses. Doesn't assume request/response ordering - a
    broadcast (e.g. the opponent's move landing) can arrive on receive()
    before the direct reply to a command a caller just sent, so callers that
    need to tell them apart should inspect the Response type themselves."""

    def __init__(self, uri):
        self.uri = uri
        self._connection = None

    async def connect(self):
        self._connection = await websockets.connect(self.uri)

    async def send_command(self, command):
        await self._connection.send(serialize(command))

    async def receive(self):
        message = await self._connection.recv()
        return deserialize(message)

    async def close(self):
        await self._connection.close()
