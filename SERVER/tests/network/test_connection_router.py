import unittest
from unittest.mock import Mock

from SERVER.network.connection_router import ConnectionRouter
from SHARED.network.protocol import (
    LoginCommand, RegisterCommand, PlayCommand, CreateRoomCommand, JoinRoomCommand, MoveCommand, GetStateCommand,
    CheckReconnectCommand, LoginSucceeded, LoginFailed, RegisterSucceeded, RegisterFailed, GameStarted, Waiting,
    PlayFailed, RoomCreated, RoomJoined, RoomJoinFailed, GameStateUpdated, ReconnectAvailable, NoReconnectAvailable,
)
from SERVER.model.position import Position


def make_router():
    game_manager = Mock()
    auth_service = Mock()
    matchmaker = Mock()
    return ConnectionRouter(game_manager, auth_service, matchmaker), game_manager, auth_service, matchmaker


class TestHandleUnknownCommand(unittest.TestCase):

    def test_returns_none_for_a_command_with_no_registered_handler(self):
        router, *_ = make_router()
        self.assertIsNone(router.handle(object()))


class TestHandleLogin(unittest.TestCase):

    def test_delegates_to_auth_service_login(self):
        router, _, auth_service, _ = make_router()
        auth_service.login.return_value = Mock(username="alice")

        router.handle(LoginCommand("alice", "hunter2"))

        auth_service.login.assert_called_once_with("alice", "hunter2")

    def test_returns_login_succeeded_with_the_users_username(self):
        router, _, auth_service, _ = make_router()
        auth_service.login.return_value = Mock(username="alice")

        response = router.handle(LoginCommand("alice", "hunter2"))

        self.assertIsInstance(response, LoginSucceeded)
        self.assertEqual(response.username, "alice")

    def test_returns_login_failed_when_auth_service_rejects_the_credentials(self):
        router, _, auth_service, _ = make_router()
        auth_service.login.return_value = None

        response = router.handle(LoginCommand("alice", "wrong"))

        self.assertIsInstance(response, LoginFailed)
        self.assertEqual(response.reason, "invalid_credentials")


class TestHandleRegister(unittest.TestCase):

    def test_delegates_to_auth_service_register(self):
        router, _, auth_service, _ = make_router()
        auth_service.register.return_value = Mock(username="alice")

        router.handle(RegisterCommand("alice", "hunter2"))

        auth_service.register.assert_called_once_with("alice", "hunter2")

    def test_returns_register_succeeded_with_the_users_username(self):
        router, _, auth_service, _ = make_router()
        auth_service.register.return_value = Mock(username="alice")

        response = router.handle(RegisterCommand("alice", "hunter2"))

        self.assertIsInstance(response, RegisterSucceeded)
        self.assertEqual(response.username, "alice")

    def test_returns_register_failed_when_the_username_is_taken(self):
        router, _, auth_service, _ = make_router()
        auth_service.register.return_value = None

        response = router.handle(RegisterCommand("alice", "hunter2"))

        self.assertIsInstance(response, RegisterFailed)
        self.assertEqual(response.reason, "username_taken")


class TestHandlePlay(unittest.TestCase):

    def test_unknown_username_returns_play_failed_and_never_touches_the_matchmaker(self):
        router, _, auth_service, matchmaker = make_router()
        auth_service.get_user.return_value = None

        response = router.handle(PlayCommand("alice"))

        self.assertIsInstance(response, PlayFailed)
        self.assertEqual(response.reason, "unknown_user")
        matchmaker.find_match.assert_not_called()

    def test_looks_up_a_match_using_the_users_rating(self):
        router, _, auth_service, matchmaker = make_router()
        auth_service.get_user.return_value = Mock(rating=1250)
        matchmaker.find_match.return_value = None

        router.handle(PlayCommand("alice"))

        matchmaker.find_match.assert_called_once_with("alice", 1250)

    def test_returns_waiting_when_no_match_is_found(self):
        router, _, auth_service, matchmaker = make_router()
        auth_service.get_user.return_value = Mock(rating=1250)
        matchmaker.find_match.return_value = None

        response = router.handle(PlayCommand("alice"))

        self.assertIsInstance(response, Waiting)

    def test_returns_game_started_with_the_new_sessions_room_id_when_matched(self):
        router, _, auth_service, matchmaker = make_router()
        auth_service.get_user.return_value = Mock(rating=1250)
        matchmaker.find_match.return_value = Mock(room_id="room-1")

        response = router.handle(PlayCommand("alice"))

        self.assertIsInstance(response, GameStarted)
        self.assertEqual(response.room_id, "room-1")

    def test_game_started_carries_the_callers_own_color(self):
        router, _, auth_service, matchmaker = make_router()
        auth_service.get_user.return_value = Mock(rating=1250)
        session = Mock(room_id="room-1")
        session.color_of.return_value = "b"
        matchmaker.find_match.return_value = session

        response = router.handle(PlayCommand("alice"))

        session.color_of.assert_called_once_with("alice")
        self.assertEqual(response.color, "b")


class TestHandleCreateRoom(unittest.TestCase):

    def test_creates_a_session_via_the_game_manager(self):
        router, game_manager, *_ = make_router()
        session = Mock(room_id="room-1")
        game_manager.create_session.return_value = session

        router.handle(CreateRoomCommand("alice"))

        game_manager.create_session.assert_called_once()

    def test_joins_the_new_session_with_the_commands_username(self):
        router, game_manager, *_ = make_router()
        session = Mock(room_id="room-1")
        game_manager.create_session.return_value = session

        router.handle(CreateRoomCommand("alice"))

        session.join.assert_called_once_with("alice")

    def test_returns_room_created_with_the_new_room_id(self):
        router, game_manager, *_ = make_router()
        game_manager.create_session.return_value = Mock(room_id="room-1")

        response = router.handle(CreateRoomCommand("alice"))

        self.assertIsInstance(response, RoomCreated)
        self.assertEqual(response.room_id, "room-1")

    def test_room_created_carries_the_creators_own_color(self):
        router, game_manager, *_ = make_router()
        session = Mock(room_id="room-1")
        session.color_of.return_value = "w"
        game_manager.create_session.return_value = session

        response = router.handle(CreateRoomCommand("alice"))

        session.color_of.assert_called_once_with("alice")
        self.assertEqual(response.color, "w")


class TestHandleJoinRoom(unittest.TestCase):

    def test_looks_up_the_session_by_room_id(self):
        router, game_manager, *_ = make_router()
        game_manager.join_session.return_value = Mock(room_id="room-1")

        router.handle(JoinRoomCommand("bob", "room-1"))

        game_manager.join_session.assert_called_once_with("room-1")

    def test_unknown_room_id_returns_room_join_failed_and_joins_nothing(self):
        router, game_manager, *_ = make_router()
        game_manager.join_session.return_value = None

        response = router.handle(JoinRoomCommand("bob", "no-such-room"))

        self.assertIsInstance(response, RoomJoinFailed)
        self.assertEqual(response.reason, "room_not_found")

    def test_joins_the_found_session_with_the_commands_username(self):
        router, game_manager, *_ = make_router()
        session = Mock(room_id="room-1")
        game_manager.join_session.return_value = session

        router.handle(JoinRoomCommand("bob", "room-1"))

        session.join.assert_called_once_with("bob")

    def test_room_joined_carries_the_joiners_own_color(self):
        router, game_manager, *_ = make_router()
        session = Mock(room_id="room-1")
        session.color_of.return_value = "b"
        game_manager.join_session.return_value = session

        response = router.handle(JoinRoomCommand("bob", "room-1"))

        session.color_of.assert_called_once_with("bob")
        self.assertEqual(response.color, "b")

    def test_returns_room_joined_with_the_sessions_current_state(self):
        router, game_manager, *_ = make_router()
        session = Mock(room_id="room-1")
        session.controller.get_state.return_value = "the_state"
        game_manager.join_session.return_value = session

        response = router.handle(JoinRoomCommand("bob", "room-1"))

        self.assertIsInstance(response, RoomJoined)
        self.assertEqual(response.room_id, "room-1")
        self.assertEqual(response.state, "the_state")


def make_session_owned_by(username, room_id="room-1", color="w"):
    """A Mock session seated so `username` owns whatever piece sits at the
    source square used in these tests."""
    session = Mock(room_id=room_id)
    session.players = {color: username}
    session.color_of.side_effect = lambda name: next(
        (c for c, u in session.players.items() if u == name), None
    )
    session.controller.game_engine.board.get_piece.return_value = Mock(
        get_color=Mock(return_value=color)
    )
    return session


class TestHandleMove(unittest.TestCase):

    def test_unknown_room_id_returns_none_and_never_touches_a_controller(self):
        router, game_manager, *_ = make_router()
        game_manager.join_session.return_value = None

        response = router.handle(MoveCommand("alice", "no-such-room", (0, 0), (0, 1)))

        self.assertIsNone(response)

    def test_converts_source_and_destination_tuples_to_positions(self):
        router, game_manager, *_ = make_router()
        session = make_session_owned_by("alice")
        game_manager.join_session.return_value = session

        router.handle(MoveCommand("alice", "room-1", (1, 2), (3, 4)))

        source, destination = session.controller.handle_move.call_args.args
        self.assertIsInstance(source, Position)
        self.assertIsInstance(destination, Position)
        self.assertEqual((source.get_row(), source.get_col()), (1, 2))
        self.assertEqual((destination.get_row(), destination.get_col()), (3, 4))

    def test_returns_game_state_updated_with_the_sessions_current_state(self):
        router, game_manager, *_ = make_router()
        session = make_session_owned_by("alice")
        session.controller.get_state.return_value = "the_state"
        game_manager.join_session.return_value = session

        response = router.handle(MoveCommand("alice", "room-1", (0, 0), (0, 1)))

        self.assertIsInstance(response, GameStateUpdated)
        self.assertEqual(response.room_id, "room-1")
        self.assertEqual(response.state, "the_state")

    def test_does_not_publish_anything_itself_move_landing_is_gamesessions_job(self):
        # _handle_move only schedules the move; MOVE_COMPLETED/GAME_ENDED are
        # published later by GameSession.advance() once time actually elapses
        # (see tests/session/test_game_session.py::TestAdvance).
        router, game_manager, *_ = make_router()
        session = make_session_owned_by("alice")
        session.controller.get_state.return_value = "the_state"
        game_manager.join_session.return_value = session

        router.handle(MoveCommand("alice", "room-1", (0, 0), (0, 1)))

        session.events.publish.assert_not_called()

    def test_moving_the_opponents_piece_never_reaches_the_controller(self):
        router, game_manager, *_ = make_router()
        session = make_session_owned_by("alice", color="w")
        session.players["b"] = "bob"
        game_manager.join_session.return_value = session

        router.handle(MoveCommand("bob", "room-1", (0, 0), (0, 1)))

        session.controller.handle_move.assert_not_called()

    def test_moving_the_opponents_piece_still_returns_the_unchanged_state(self):
        # Rejected moves aren't errors - they just don't change anything, so
        # the client sees the same state come back on the next update.
        router, game_manager, *_ = make_router()
        session = make_session_owned_by("alice", color="w")
        session.players["b"] = "bob"
        session.controller.get_state.return_value = "the_state"
        game_manager.join_session.return_value = session

        response = router.handle(MoveCommand("bob", "room-1", (0, 0), (0, 1)))

        self.assertIsInstance(response, GameStateUpdated)
        self.assertEqual(response.state, "the_state")

    def test_moving_from_an_empty_square_never_reaches_the_controller(self):
        router, game_manager, *_ = make_router()
        session = Mock(room_id="room-1")
        session.players = {"w": "alice", "b": "bob"}
        session.controller.game_engine.board.get_piece.return_value = None
        game_manager.join_session.return_value = session

        router.handle(MoveCommand("alice", "room-1", (0, 0), (0, 1)))

        session.controller.handle_move.assert_not_called()

    def test_a_spectator_can_never_move_anything(self):
        router, game_manager, *_ = make_router()
        session = make_session_owned_by("alice", color="w")
        session.players["b"] = "bob"
        game_manager.join_session.return_value = session

        router.handle(MoveCommand("carol_spectator", "room-1", (0, 0), (0, 1)))

        session.controller.handle_move.assert_not_called()

    def test_an_out_of_bounds_source_never_reaches_the_board(self):
        # A real Board.get_piece() would raise IndexError on an out-of-range
        # position - inside_bounds() must be checked before anything touches
        # the board at all, not just before the ownership lookup.
        router, game_manager, *_ = make_router()
        session = make_session_owned_by("alice")
        session.controller.game_engine.board.inside_bounds.return_value = False
        game_manager.join_session.return_value = session

        router.handle(MoveCommand("alice", "room-1", (99, 99), (0, 1)))

        session.controller.game_engine.board.get_piece.assert_not_called()
        session.controller.handle_move.assert_not_called()

    def test_an_out_of_bounds_destination_never_reaches_the_controller(self):
        router, game_manager, *_ = make_router()
        session = make_session_owned_by("alice")
        real_inside_bounds = lambda position: position.get_row() < 8 and position.get_col() < 8
        session.controller.game_engine.board.inside_bounds.side_effect = real_inside_bounds
        game_manager.join_session.return_value = session

        router.handle(MoveCommand("alice", "room-1", (0, 0), (99, 99)))

        session.controller.handle_move.assert_not_called()

    def test_out_of_bounds_move_still_returns_the_unchanged_state(self):
        router, game_manager, *_ = make_router()
        session = make_session_owned_by("alice")
        session.controller.game_engine.board.inside_bounds.return_value = False
        session.controller.get_state.return_value = "the_state"
        game_manager.join_session.return_value = session

        response = router.handle(MoveCommand("alice", "room-1", (99, 99), (0, 1)))

        self.assertIsInstance(response, GameStateUpdated)
        self.assertEqual(response.state, "the_state")


class TestHandleGetState(unittest.TestCase):

    def test_unknown_room_id_returns_none(self):
        router, game_manager, *_ = make_router()
        game_manager.join_session.return_value = None

        response = router.handle(GetStateCommand("no-such-room"))

        self.assertIsNone(response)

    def test_returns_game_state_updated_without_joining_or_touching_the_controller(self):
        router, game_manager, *_ = make_router()
        session = Mock(room_id="room-1")
        session.controller.get_state.return_value = "the_state"
        game_manager.join_session.return_value = session

        response = router.handle(GetStateCommand("room-1"))

        self.assertIsInstance(response, GameStateUpdated)
        self.assertEqual(response.room_id, "room-1")
        self.assertEqual(response.state, "the_state")
        session.join.assert_not_called()
        session.controller.handle_move.assert_not_called()


class TestHandleCheckReconnect(unittest.TestCase):

    def test_no_reconnectable_session_returns_no_reconnect_available(self):
        router, game_manager, *_ = make_router()
        game_manager.find_reconnectable_session.return_value = None

        response = router.handle(CheckReconnectCommand("alice"))

        self.assertIsInstance(response, NoReconnectAvailable)

    def test_looks_up_the_reconnectable_session_by_username(self):
        router, game_manager, *_ = make_router()
        game_manager.find_reconnectable_session.return_value = None

        router.handle(CheckReconnectCommand("alice"))

        game_manager.find_reconnectable_session.assert_called_once_with("alice")

    def test_a_reconnectable_session_returns_its_room_id_and_the_players_color(self):
        router, game_manager, *_ = make_router()
        session = Mock(room_id="room-1")
        session.color_of.return_value = "b"
        game_manager.find_reconnectable_session.return_value = session

        response = router.handle(CheckReconnectCommand("bob"))

        self.assertIsInstance(response, ReconnectAvailable)
        self.assertEqual(response.room_id, "room-1")
        self.assertEqual(response.color, "b")
        session.color_of.assert_called_once_with("bob")


class TestEndToEndThroughRealGameManagerAndController(unittest.TestCase):
    """Proves the exact chain requested: MoveCommand -> game_manager lookup
    -> session.controller.handle_move() -> a real GameEngine move, with no
    fake/mock collaborators and no transport at all."""

    def test_a_legal_move_actually_moves_the_piece_on_the_real_board(self):
        from SERVER.session.game_manager import GameManager
        from SERVER.model.position import Position as RealPosition

        game_manager = GameManager()
        router = ConnectionRouter(game_manager, Mock(), Mock())

        created = router.handle(CreateRoomCommand("alice"))
        router.handle(JoinRoomCommand("bob", created.room_id))

        # pictures/board.csv puts white's pawns on row 6; a single-step
        # forward move to row 5 is legal and unambiguous either way.
        board = game_manager.join_session(created.room_id).controller.game_engine.board
        piece = board.get_piece(RealPosition(6, 0))
        self.assertIsNotNone(piece)

        response = router.handle(MoveCommand("alice", created.room_id, (6, 0), (5, 0)))

        self.assertIsInstance(response, GameStateUpdated)
        # The move is scheduled as an in-flight Motion rather than landing
        # instantly, so right after handle_move() it's still resolving.
        self.assertEqual(len(response.state.motions), 1)
        self.assertIs(response.state.motions[0].piece, piece)

    def test_an_out_of_bounds_move_against_a_real_board_does_not_raise(self):
        # Regression: a click landing outside the board (e.g. in the score
        # panel next to it) used to reach Board.get_piece() unchecked and
        # crash the connection with an IndexError.
        from SERVER.session.game_manager import GameManager

        game_manager = GameManager()
        router = ConnectionRouter(game_manager, Mock(), Mock())

        created = router.handle(CreateRoomCommand("alice"))
        router.handle(JoinRoomCommand("bob", created.room_id))

        response = router.handle(MoveCommand("alice", created.room_id, (6, 0), (99, 99)))

        self.assertIsInstance(response, GameStateUpdated)
        self.assertEqual(response.state.motions, [])

    def test_a_move_reaches_a_network_publisher_once_the_session_advances_past_landing(self):
        # MoveCommand only schedules the move (see the test above - it's
        # still in-flight right after handle()); MOVE_COMPLETED only fires
        # once GameSession.advance() detects it actually landed.
        from SERVER.session.game_manager import GameManager
        from SERVER.network.network_publisher import NetworkPublisher

        game_manager = GameManager()
        router = ConnectionRouter(game_manager, Mock(), Mock())

        created = router.handle(CreateRoomCommand("alice"))
        router.handle(JoinRoomCommand("bob", created.room_id))
        session = game_manager.join_session(created.room_id)

        sent = []
        NetworkPublisher(session.events, sink=sent.append)

        router.handle(MoveCommand("alice", created.room_id, (6, 0), (5, 0)))
        self.assertEqual(sent, [])  # not yet - still mid-flight

        session.advance(1000)  # long enough for the move to land

        self.assertEqual(len(sent), 1)
        self.assertIsInstance(sent[0], GameStateUpdated)
        self.assertEqual(sent[0].room_id, created.room_id)


class TestLoginEndToEndWithRealAuthService(unittest.TestCase):
    """No mocks: a real AuthService backed by a real (in-memory) SQLite
    repository, reached the same way the router would in production."""

    def make_router_with_real_auth(self):
        from SERVER.accounts.auth_service import AuthService
        from SERVER.accounts.sqlite_user_repository import SqliteUserRepository

        auth_service = AuthService(SqliteUserRepository(":memory:"))
        return ConnectionRouter(Mock(), auth_service, Mock()), auth_service

    def test_registered_user_can_log_in_through_the_router(self):
        router, auth_service = self.make_router_with_real_auth()
        auth_service.register("alice", "hunter2")

        response = router.handle(LoginCommand("alice", "hunter2"))

        self.assertIsInstance(response, LoginSucceeded)
        self.assertEqual(response.username, "alice")

    def test_wrong_password_fails_through_the_router(self):
        router, auth_service = self.make_router_with_real_auth()
        auth_service.register("alice", "hunter2")

        response = router.handle(LoginCommand("alice", "wrong"))

        self.assertIsInstance(response, LoginFailed)

    def test_unregistered_username_fails_through_the_router(self):
        router, _ = self.make_router_with_real_auth()

        response = router.handle(LoginCommand("nobody", "whatever"))

        self.assertIsInstance(response, LoginFailed)


if __name__ == "__main__":
    unittest.main()
