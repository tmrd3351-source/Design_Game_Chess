import asyncio
import unittest

from SERVER.accounts.auth_service import AuthService
from SERVER.accounts.sqlite_user_repository import SqliteUserRepository
from SERVER.session.game_manager import GameManager
from SERVER.session.matchmaker import Matchmaker
from SERVER.session.session_ticker import SessionTicker
from SERVER.network.connection_router import ConnectionRouter
from SERVER.network.websocket_server import WebSocketServer
from CLIENT.network.websocket_client import WebSocketClient
from SHARED.network.protocol import (
    LoginCommand, PlayCommand, CreateRoomCommand, JoinRoomCommand, MoveCommand, CheckReconnectCommand,
    LoginSucceeded, LoginFailed, RoomCreated, RoomJoined, RoomJoinFailed,
    GameStarted, Waiting, GameStateUpdated, NoReconnectAvailable,
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
        self.assertEqual(created.color, "w")

        await bob.send_command(JoinRoomCommand("bob", created.room_id))
        joined = await bob.receive()

        self.assertIsInstance(joined, RoomJoined)
        self.assertEqual(joined.room_id, created.room_id)
        self.assertEqual(joined.color, "b")
        self.assertEqual(joined.state["board"]["rows"], 8)

    async def test_room_creator_is_pushed_a_notification_once_someone_joins(self):
        # The creator's own CreateRoomCommand reply only has one seat filled
        # - she's not told the game started until bob actually joins, which
        # arrives as an unsolicited push on her own connection.
        alice = await self.make_client()
        bob = await self.make_client()

        await alice.send_command(CreateRoomCommand("alice"))
        created = await alice.receive()

        await bob.send_command(JoinRoomCommand("bob", created.room_id))
        bob_reply = await bob.receive()
        self.assertIsInstance(bob_reply, RoomJoined)

        alice_push = await asyncio.wait_for(alice.receive(), timeout=5)
        self.assertIsInstance(alice_push, RoomJoined)
        self.assertEqual(alice_push.room_id, created.room_id)
        self.assertEqual(alice_push.color, "w")

    async def test_joining_an_unknown_room_id_fails(self):
        bob = await self.make_client()

        await bob.send_command(JoinRoomCommand("bob", "no-such-room"))
        response = await bob.receive()

        self.assertIsInstance(response, RoomJoinFailed)
        self.assertEqual(response.reason, "room_not_found")

    async def test_a_move_broadcasts_to_both_connections_once_it_lands(self):
        alice = await self.make_client()
        bob = await self.make_client()

        await alice.send_command(CreateRoomCommand("alice"))
        created = await alice.receive()
        await bob.send_command(JoinRoomCommand("bob", created.room_id))
        await bob.receive()
        await alice.receive()  # alice's own "game started" push from bob joining

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

        # alice queued first, so she's seated "w"; bob's PlayCommand
        # triggered the match, so he's seated "b" - each must be told their
        # own color, not the other player's.
        self.assertEqual(alice_push.color, "w")
        self.assertEqual(bob_reply.color, "b")

    async def test_check_reconnect_over_a_real_socket_when_nothing_pending(self):
        client = await self.make_client()

        await client.send_command(CheckReconnectCommand("alice"))
        response = await client.receive()

        self.assertIsInstance(response, NoReconnectAvailable)


class TestReconnectAfterDisconnect(unittest.IsolatedAsyncioTestCase):
    """A tiny grace period (well under a second) so these run fast instead
    of waiting on the real 20s default - otherwise identical real-server/
    real-socket setup to TestWebSocketServer above."""

    # Generous relative to real connection-teardown/setup overhead in the
    # test itself (closing and opening real sockets isn't instant, and gets
    # less predictable as more of these run in the same process) - the
    # "reconnect in time" tests only sleep a small fraction of this.
    GRACE_SECONDS = 3

    async def asyncSetUp(self):
        user_repository = SqliteUserRepository(":memory:")
        auth_service = AuthService(user_repository)
        auth_service.register("alice", "pw1")
        auth_service.register("bob", "pw2")
        game_manager = GameManager()
        matchmaker = Matchmaker(game_manager)
        connection_router = ConnectionRouter(game_manager, auth_service, matchmaker)
        session_ticker = SessionTicker(game_manager)

        self.server = WebSocketServer(connection_router, game_manager, session_ticker, port=0,
                                       disconnect_grace_seconds=self.GRACE_SECONDS)
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

    async def start_a_game(self):
        alice = await self.make_client()
        bob = await self.make_client()
        await alice.send_command(CreateRoomCommand("alice"))
        created = await alice.receive()
        await bob.send_command(JoinRoomCommand("bob", created.room_id))
        await bob.receive()
        await alice.receive()  # alice's own "game started" push
        return alice, bob, created.room_id

    async def test_reconnecting_within_the_grace_period_restores_the_same_seat(self):
        alice, bob, room_id = await self.start_a_game()

        await alice.close()
        await asyncio.sleep(0.1)  # comfortably within the grace window
        reconnected = await self.make_client()
        await reconnected.send_command(JoinRoomCommand("alice", room_id))
        response = await reconnected.receive()

        self.assertIsInstance(response, RoomJoined)
        self.assertEqual(response.color, "w")
        self.assertFalse(response.state["game_over"])

    async def test_reconnecting_in_time_means_the_other_player_never_sees_a_forfeit(self):
        alice, bob, room_id = await self.start_a_game()

        await alice.close()
        reconnected = await self.make_client()
        await reconnected.send_command(JoinRoomCommand("alice", room_id))
        await reconnected.receive()

        # Give the original grace-period timer time to fire if reconnecting
        # hadn't actually cancelled/prevented it - bob must see nothing.
        with self.assertRaises(asyncio.TimeoutError):
            await asyncio.wait_for(bob.receive(), timeout=self.GRACE_SECONDS * 2)

    async def test_not_reconnecting_in_time_forfeits_to_the_other_player(self):
        alice, bob, room_id = await self.start_a_game()

        await alice.close()

        forfeit_broadcast = await asyncio.wait_for(bob.receive(), timeout=self.GRACE_SECONDS + 2)

        self.assertIsInstance(forfeit_broadcast, GameStateUpdated)
        self.assertTrue(forfeit_broadcast.state["game_over"])
        self.assertEqual(forfeit_broadcast.state["winner"], "b")

    async def test_forfeited_game_is_no_longer_reconnectable_afterward(self):
        alice, bob, room_id = await self.start_a_game()

        await alice.close()
        await asyncio.wait_for(bob.receive(), timeout=self.GRACE_SECONDS + 2)  # forfeit lands

        late_client = await self.make_client()
        await late_client.send_command(CheckReconnectCommand("alice"))
        response = await late_client.receive()

        self.assertIsInstance(response, NoReconnectAvailable)


if __name__ == "__main__":
    unittest.main()
