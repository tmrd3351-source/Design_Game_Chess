import asyncio
import threading
import time
import unittest

from SERVER.accounts.auth_service import AuthService
from SERVER.accounts.sqlite_user_repository import SqliteUserRepository
from SERVER.session.game_manager import GameManager
from SERVER.session.matchmaker import Matchmaker
from SERVER.session.session_ticker import SessionTicker
from SERVER.network.connection_router import ConnectionRouter
from SERVER.network.websocket_server import WebSocketServer
from CLIENT.network.network_session import NetworkSession
from SHARED.network.protocol import PlayCommand, Waiting, GameStarted


class TestNetworkSession(unittest.TestCase):
    """No mocks: a real WebSocketServer on a background thread (its own
    event loop), driven by real NetworkSessions on the main thread (each
    with their own event loop) - proves poll() survives being called
    repeatedly with a near-zero timeout, exactly how a render loop uses it
    every frame. A naive wait_for()-with-cancellation implementation of
    poll() silently lost messages under this exact pattern."""

    @classmethod
    def setUpClass(cls):
        thread_ready = threading.Event()
        server_holder = {}

        def _run_server():
            # Everything - including the sqlite3 connection - is built and
            # used entirely on this one thread; sqlite3 connections can't
            # cross threads, and in real usage (server.py) the whole stack
            # already lives on a single asyncio-run() thread anyway.
            user_repository = SqliteUserRepository(":memory:")
            auth_service = AuthService(user_repository)
            for username in ("poll_alice", "poll_bob", "solo_seeker"):
                auth_service.register(username, "password")
            game_manager = GameManager()
            matchmaker = Matchmaker(game_manager)
            connection_router = ConnectionRouter(game_manager, auth_service, matchmaker)
            session_ticker = SessionTicker(game_manager)
            server = WebSocketServer(connection_router, game_manager, session_ticker, port=0)
            server_holder["server"] = server

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            async def _serve():
                task = asyncio.ensure_future(server.start())
                await server.ready.wait()
                thread_ready.set()
                await task

            loop.run_until_complete(_serve())

        cls.server_thread = threading.Thread(target=_run_server, daemon=True)
        cls.server_thread.start()
        if not thread_ready.wait(timeout=5):
            raise RuntimeError("server did not become ready in time")
        cls.server = server_holder["server"]

    def make_session(self):
        return NetworkSession(f"ws://localhost:{self.server.port}")

    def test_polling_with_a_zero_timeout_repeatedly_still_receives_the_push(self):
        alice = self.make_session()
        bob = self.make_session()

        alice.send(PlayCommand("poll_alice"))
        self.assertIsInstance(alice.poll(timeout=1), Waiting)

        bob.send(PlayCommand("poll_bob"))
        bob_response = bob.poll(timeout=1)
        self.assertIsInstance(bob_response, GameStarted)

        # The exact pattern a render loop uses: many short/zero-timeout
        # polls in a row, each one a separate call, rather than one
        # generous wait - this is what exposed the message-loss bug.
        received = None
        for _ in range(50):
            received = alice.poll(timeout=0.0)
            if received is not None:
                break
            time.sleep(0.05)

        self.assertIsInstance(received, GameStarted)
        self.assertEqual(received.room_id, bob_response.room_id)

        alice.close()
        bob.close()

    def test_poll_returns_none_immediately_when_nothing_has_arrived(self):
        session = self.make_session()
        self.assertIsNone(session.poll(timeout=0.0))
        session.close()

    def test_send_then_poll_round_trip(self):
        session = self.make_session()
        session.send(PlayCommand("solo_seeker"))

        response = session.poll(timeout=2)

        self.assertIsInstance(response, Waiting)
        session.close()


if __name__ == "__main__":
    unittest.main()
