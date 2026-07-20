import asyncio

from network.websocket_client import WebSocketClient


class NetworkSession:
    """A persistent WebSocketClient connection driven by its own event loop,
    exposing plain synchronous send()/poll()/close() - so a synchronous cv2
    render loop can send Commands and check each frame for a Response
    (including an unsolicited server push, like a matched opponent) without
    ever blocking on network I/O, and without needing a background thread.

    poll() keeps one persistent receive Task alive across calls rather than
    starting a fresh recv() and cancelling it on every short-timeout poll -
    cancelling an in-flight recv() races with a frame that's still arriving
    and can lose it, since it's never given a later poll to complete on."""

    def __init__(self, server_uri):
        self._loop = asyncio.new_event_loop()
        self._client = WebSocketClient(server_uri)
        self._loop.run_until_complete(self._client.connect())
        self._pending_receive = None

    def send(self, command):
        self._loop.run_until_complete(self._client.send_command(command))

    def poll(self, timeout=0.0):
        """Returns the next Response if one has arrived (or arrives within
        `timeout` seconds), otherwise None. Never loses a message - if
        nothing is ready yet, the same receive keeps waiting in the
        background for the next poll() to check on."""
        if self._pending_receive is None:
            self._pending_receive = self._loop.create_task(self._client.receive())

        done, _ = self._loop.run_until_complete(
            asyncio.wait([self._pending_receive], timeout=timeout)
        )
        if not done:
            return None

        result = self._pending_receive.result()
        self._pending_receive = None
        return result

    def close(self):
        if self._pending_receive is not None:
            self._pending_receive.cancel()
        self._loop.run_until_complete(self._client.close())
        self._loop.close()
