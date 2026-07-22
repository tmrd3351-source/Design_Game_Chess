import unittest

from SHARED.network.serialization import serialize, deserialize
from SHARED.network.protocol import (
    LoginCommand, PlayCommand, CreateRoomCommand, JoinRoomCommand, MoveCommand,
    LoginSucceeded, LoginFailed, GameStarted, Waiting, RoomCreated, GameStateUpdated,
)
from SHARED.model.board import Board
from SHARED.model.piece import Piece
from SHARED.model.position import Position
from SHARED.model.game_state import GameState


class TestRoundTrip(unittest.TestCase):

    def test_login_command_round_trips(self):
        original = LoginCommand("alice", "hunter2")
        result = deserialize(serialize(original))
        self.assertIsInstance(result, LoginCommand)
        self.assertEqual(result.username, "alice")
        self.assertEqual(result.password, "hunter2")

    def test_play_command_round_trips(self):
        result = deserialize(serialize(PlayCommand("alice")))
        self.assertIsInstance(result, PlayCommand)
        self.assertEqual(result.username, "alice")

    def test_create_room_command_round_trips(self):
        result = deserialize(serialize(CreateRoomCommand("alice")))
        self.assertIsInstance(result, CreateRoomCommand)
        self.assertEqual(result.username, "alice")

    def test_join_room_command_round_trips(self):
        result = deserialize(serialize(JoinRoomCommand("alice", "room-1")))
        self.assertIsInstance(result, JoinRoomCommand)
        self.assertEqual(result.username, "alice")
        self.assertEqual(result.room_id, "room-1")

    def test_move_command_round_trips_tuples_as_lists(self):
        original = MoveCommand("alice", "room-1", (1, 2), (3, 4))
        result = deserialize(serialize(original))
        self.assertIsInstance(result, MoveCommand)
        # JSON has no tuple type - source/destination come back as lists,
        # which is fine since ConnectionRouter unpacks them positionally.
        self.assertEqual(list(result.source), [1, 2])
        self.assertEqual(list(result.destination), [3, 4])

    def test_login_succeeded_round_trips(self):
        result = deserialize(serialize(LoginSucceeded("alice")))
        self.assertIsInstance(result, LoginSucceeded)
        self.assertEqual(result.username, "alice")

    def test_login_failed_round_trips(self):
        result = deserialize(serialize(LoginFailed("invalid_credentials")))
        self.assertIsInstance(result, LoginFailed)
        self.assertEqual(result.reason, "invalid_credentials")

    def test_room_created_round_trips(self):
        result = deserialize(serialize(RoomCreated("room-1")))
        self.assertIsInstance(result, RoomCreated)
        self.assertEqual(result.room_id, "room-1")

    def test_game_started_round_trips(self):
        result = deserialize(serialize(GameStarted("room-1")))
        self.assertIsInstance(result, GameStarted)
        self.assertEqual(result.room_id, "room-1")

    def test_waiting_round_trips(self):
        result = deserialize(serialize(Waiting()))
        self.assertIsInstance(result, Waiting)

    def test_game_state_updated_round_trips_a_plain_dict_state(self):
        original = GameStateUpdated("room-1", {"rows": 8, "cols": 8})
        result = deserialize(serialize(original))
        self.assertIsInstance(result, GameStateUpdated)
        self.assertEqual(result.room_id, "room-1")
        self.assertEqual(result.state, {"rows": 8, "cols": 8})

    def test_game_state_updated_serializes_a_real_game_state_without_crashing(self):
        # GameState wraps real Board/Piece/Motion objects, which aren't
        # JSON-serializable by default - this is the actual shape
        # ConnectionRouter responses carry in production.
        board = Board(3, 3)
        board.add_piece(Piece(1, "w", "K", Position(0, 0)))
        original = GameStateUpdated("room-1", GameState(board, None, False))

        result = deserialize(serialize(original))

        self.assertIsInstance(result, GameStateUpdated)
        self.assertEqual(result.room_id, "room-1")
        self.assertEqual(result.state["board"]["rows"], 3)
        self.assertEqual(result.state["board"]["pieces"][0]["id"], 1)
        self.assertFalse(result.state["game_over"])


if __name__ == "__main__":
    unittest.main()
