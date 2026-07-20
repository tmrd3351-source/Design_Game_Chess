import unittest

from network.protocol import (
    LoginCommand, PlayCommand, CreateRoomCommand, JoinRoomCommand, MoveCommand,
    LoginSucceeded, LoginFailed, RoomCreated, GameStarted, GameStateUpdated, Waiting,
)


class TestCommands(unittest.TestCase):

    def test_login_command_stores_username_and_password(self):
        command = LoginCommand("alice", "hunter2")
        self.assertEqual(command.username, "alice")
        self.assertEqual(command.password, "hunter2")

    def test_play_command_stores_username(self):
        self.assertEqual(PlayCommand("alice").username, "alice")

    def test_create_room_command_stores_username(self):
        self.assertEqual(CreateRoomCommand("alice").username, "alice")

    def test_join_room_command_stores_username_and_room_id(self):
        command = JoinRoomCommand("alice", "room-1")
        self.assertEqual(command.username, "alice")
        self.assertEqual(command.room_id, "room-1")

    def test_move_command_stores_all_fields(self):
        command = MoveCommand("alice", "room-1", (1, 2), (3, 4))
        self.assertEqual(command.username, "alice")
        self.assertEqual(command.room_id, "room-1")
        self.assertEqual(command.source, (1, 2))
        self.assertEqual(command.destination, (3, 4))


class TestResponses(unittest.TestCase):

    def test_login_succeeded_stores_username(self):
        self.assertEqual(LoginSucceeded("alice").username, "alice")

    def test_login_failed_stores_reason(self):
        self.assertEqual(LoginFailed("invalid_credentials").reason, "invalid_credentials")

    def test_room_created_stores_room_id(self):
        self.assertEqual(RoomCreated("room-1").room_id, "room-1")

    def test_game_started_stores_room_id(self):
        self.assertEqual(GameStarted("room-1").room_id, "room-1")

    def test_game_state_updated_stores_room_id_and_state(self):
        state = object()
        response = GameStateUpdated("room-1", state)
        self.assertEqual(response.room_id, "room-1")
        self.assertIs(response.state, state)

    def test_waiting_can_be_constructed(self):
        Waiting()  # must not raise


if __name__ == "__main__":
    unittest.main()
