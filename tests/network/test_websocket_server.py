import asyncio
import unittest

from accounts.auth_service import AuthService
from accounts.sqlite_user_repository import SqliteUserRepository
from session.game_manager import GameManager
from session.matchmaker import Matchmaker
from session.session_ticker import SessionTicker
from network.connection_router import ConnectionRouter
from network.websocket_server import WebSocketServer
from network.websocket_client import WebSocketClient
from network.protocol import (
    LoginCommand, PlayCommand, CreateRoomCommand, JoinRoomCommand, MoveCommand,
    LoginSucceeded, LoginFailed, RoomCreated, GameStarted, Waiting, GameStateUpdated,
)


class TestWebSocketServer(unittest.IsolatedAsyncioTestCase):
    """No mocks anywhere: a real WebSocketServer listening on a real
    (OS-assigned) localhost port, driven entirely through real
    WebSocketClient connections - the actual production transport."""

    async def asyncSetUp(self):
        user_repository = SqliteUserRepository(":memory:")
        auth_service = AuthService(user_repository)
        auth_service.register("alice", "pw1")
        auth_service.register("bob", "pw2")
        game_manager = GameManager()
        matchmaker = Matchmaker(game_manager)
        connection_router = ConnectionRouter(game_manager, auth_service, matchmaker)
        session_ticker = SessionTicker(game_manager)

        self.server = WebSocketServer(connection_router, game_manager, session_ticker, port=0)
        self.server_task = asyncio.create_task(self.server.start())
        await self.server.ready.wait()
        self.clients = []

    async def asyncTearDown(self):
        for client in self.clients:
            await client.close()
        self.server_task.cancel()
        try:
            await self.server_task
        except asyncio.CancelledError:
            pass

    async def make_client(self):
        client = WebSocketClient(f"ws://localhost:{self.server.port}")
        await client.connect()
        self.clients.append(client)
        return client

    async def test_login_round_trip_over_a_real_socket(self):
        client = await self.make_client()

        await client.send_command(LoginCommand("alice", "pw1"))
        response = await client.receive()

        self.assertIsInstance(response, LoginSucceeded)
        self.assertEqual(response.username, "alice")

    async def test_wrong_password_over_a_real_socket(self):
        client = await self.make_client()

        await client.send_command(LoginCommand("alice", "wrong"))
        response = await client.receive()

        self.assertIsInstance(response, LoginFailed)

    async def test_create_and_join_room_over_two_real_connections(self):
        alice = await self.make_client()
        bob = await self.make_client()

        await alice.send_command(CreateRoomCommand("alice"))
        created = await alice.receive()
        self.assertIsInstance(created, RoomCreated)

        await bob.send_command(JoinRoomCommand("bob", created.room_id))
        joined = await bob.receive()

        self.assertIsInstance(joined, GameStateUpdated)
        self.assertEqual(joined.room_id, created.room_id)
        self.assertEqual(joined.state["board"]["rows"], 8)

    async def test_a_move_broadcasts_to_both_connections_once_it_lands(self):
        alice = await self.make_client()
        bob = await self.make_client()

        await alice.send_command(CreateRoomCommand("alice"))
        created = await alice.receive()
        await bob.send_command(JoinRoomCommand("bob", created.room_id))
        await bob.receive()

        await alice.send_command(MoveCommand("alice", created.room_id, (6, 0), (5, 0)))
        immediate_reply = await alice.receive()
        self.assertIsInstance(immediate_reply, GameStateUpdated)
        # Still in-flight right after scheduling - one pending motion.
        self.assertEqual(len(immediate_reply.state["motions"]), 1)

        # The server ticks every 100ms; MOVE_TIME is 1000ms, so give it a
        # few seconds of real wall-clock time for the motion to land and
        # NetworkPublisher to broadcast the result to both connections.
        alice_broadcast = await asyncio.wait_for(alice.receive(), timeout=5)
        bob_broadcast = await asyncio.wait_for(bob.receive(), timeout=5)

        self.assertIsInstance(alice_broadcast, GameStateUpdated)
        self.assertIsInstance(bob_broadcast, GameStateUpdated)
        self.assertEqual(alice_broadcast.state["motions"], [])
        self.assertEqual(bob_broadcast.state["motions"], [])

    async def test_matchmaking_notifies_the_already_waiting_player_too(self):
        # alice's PlayCommand only gets Waiting() as its direct reply - she's
        # not yet tracked under any room, so this proves the server pushes
        # GameStarted to her connection separately once bob matches her,
        # rather than only replying to whoever's message triggered the match.
        alice = await self.make_client()
        bob = await self.make_client()

        await alice.send_command(PlayCommand("alice"))
        alice_first_reply = await alice.receive()
        self.assertIsInstance(alice_first_reply, Waiting)

        await bob.send_command(PlayCommand("bob"))
        bob_reply = await bob.receive()
        self.assertIsInstance(bob_reply, GameStarted)

        alice_push = await asyncio.wait_for(alice.receive(), timeout=5)
        self.assertIsInstance(alice_push, GameStarted)
        self.assertEqual(alice_push.room_id, bob_reply.room_id)


if __name__ == "__main__":
    unittest.main()
