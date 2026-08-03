import unittest

from SHARED.network.protocol import (
    LoginCommand, RegisterCommand, PlayCommand, CreateRoomCommand, JoinRoomCommand, MoveCommand, GetStateCommand,
    CheckReconnectCommand, LoginSucceeded, LoginFailed, RegisterSucceeded, RegisterFailed, RoomCreated, RoomJoined,
    RoomJoinFailed, GameStarted, GameStateUpdated, Waiting, PlayFailed, ReconnectAvailable, NoReconnectAvailable,
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

    def test_register_command_stores_username_and_password(self):
        command = RegisterCommand("alice", "hunter2")
        self.assertEqual(command.username, "alice")
        self.assertEqual(command.password, "hunter2")

    def test_get_state_command_stores_username_and_room_id(self):
        command = GetStateCommand("alice", "room-1")
        self.assertEqual(command.username, "alice")
        self.assertEqual(command.room_id, "room-1")

    def test_check_reconnect_command_stores_username(self):
        self.assertEqual(CheckReconnectCommand("alice").username, "alice")


class TestResponses(unittest.TestCase):

    def test_login_succeeded_stores_username(self):
        self.assertEqual(LoginSucceeded("alice").username, "alice")

    def test_login_failed_stores_reason(self):
        self.assertEqual(LoginFailed("invalid_credentials").reason, "invalid_credentials")

    def test_register_succeeded_stores_username(self):
        self.assertEqual(RegisterSucceeded("alice").username, "alice")

    def test_register_failed_stores_reason(self):
        self.assertEqual(RegisterFailed("username_taken").reason, "username_taken")

    def test_room_created_stores_room_id(self):
        self.assertEqual(RoomCreated("room-1").room_id, "room-1")

    def test_room_created_stores_the_creators_own_color(self):
        self.assertEqual(RoomCreated("room-1", "w").color, "w")

    def test_room_created_color_defaults_to_none(self):
        self.assertIsNone(RoomCreated("room-1").color)

    def test_room_joined_stores_room_id_color_and_state(self):
        state = object()
        response = RoomJoined("room-1", "b", state)
        self.assertEqual(response.room_id, "room-1")
        self.assertEqual(response.color, "b")
        self.assertIs(response.state, state)

    def test_room_join_failed_stores_reason(self):
        self.assertEqual(RoomJoinFailed("room_not_found").reason, "room_not_found")

    def test_game_started_stores_room_id(self):
        self.assertEqual(GameStarted("room-1").room_id, "room-1")

    def test_game_started_stores_the_recipients_color(self):
        self.assertEqual(GameStarted("room-1", "w").color, "w")

    def test_game_started_color_defaults_to_none(self):
        self.assertIsNone(GameStarted("room-1").color)

    def test_game_state_updated_stores_room_id_and_state(self):
        state = object()
        response = GameStateUpdated("room-1", state)
        self.assertEqual(response.room_id, "room-1")
        self.assertIs(response.state, state)

    def test_waiting_can_be_constructed(self):
        Waiting()  # must not raise

    def test_play_failed_stores_reason(self):
        self.assertEqual(PlayFailed("unknown_user").reason, "unknown_user")

    def test_reconnect_available_stores_room_id_and_color(self):
        response = ReconnectAvailable("room-1", "w")
        self.assertEqual(response.room_id, "room-1")
        self.assertEqual(response.color, "w")

    def test_no_reconnect_available_can_be_constructed(self):
        NoReconnectAvailable()  # must not raise


if __name__ == "__main__":
    unittest.main()
