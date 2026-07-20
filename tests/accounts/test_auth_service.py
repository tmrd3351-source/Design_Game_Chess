import secrets
import unittest
from unittest.mock import Mock

from accounts.auth_service import AuthService, STARTING_RATING, _hash_password
from accounts.sqlite_user_repository import SqliteUserRepository
from accounts.user_repository import User


def make_auth_service():
    user_repository = Mock()
    return AuthService(user_repository), user_repository


def make_stored_user(username, password, rating=1200):
    salt = secrets.token_hex(16)
    return User(username, f"{salt}:{_hash_password(password, salt)}", rating)


class TestGetUser(unittest.TestCase):

    def test_delegates_to_the_repositorys_find_by_username(self):
        auth_service, user_repository = make_auth_service()
        stored_user = User("alice", "hash", 1200)
        user_repository.find_by_username.return_value = stored_user

        result = auth_service.get_user("alice")

        user_repository.find_by_username.assert_called_once_with("alice")
        self.assertIs(result, stored_user)

    def test_returns_none_for_an_unknown_username(self):
        auth_service, user_repository = make_auth_service()
        user_repository.find_by_username.return_value = None

        self.assertIsNone(auth_service.get_user("nobody"))


class TestRegister(unittest.TestCase):

    def test_rejects_a_username_that_already_exists(self):
        auth_service, user_repository = make_auth_service()
        user_repository.find_by_username.return_value = User("alice", "hash", 1200)

        result = auth_service.register("alice", "hunter2")

        self.assertIsNone(result)
        user_repository.create_user.assert_not_called()

    def test_creates_a_new_user_at_the_starting_rating(self):
        auth_service, user_repository = make_auth_service()
        user_repository.find_by_username.return_value = None

        auth_service.register("alice", "hunter2")

        user_repository.create_user.assert_called_once()
        args = user_repository.create_user.call_args.args
        self.assertEqual(args[0], "alice")
        self.assertEqual(args[2], STARTING_RATING)

    def test_never_passes_the_plaintext_password_to_the_repository(self):
        auth_service, user_repository = make_auth_service()
        user_repository.find_by_username.return_value = None

        auth_service.register("alice", "hunter2")

        password_hash = user_repository.create_user.call_args.args[1]
        self.assertNotIn("hunter2", password_hash)

    def test_returns_the_repositorys_created_user(self):
        auth_service, user_repository = make_auth_service()
        user_repository.find_by_username.return_value = None
        created = User("alice", "hash", STARTING_RATING)
        user_repository.create_user.return_value = created

        result = auth_service.register("alice", "hunter2")

        self.assertIs(result, created)


class TestLogin(unittest.TestCase):

    def test_returns_none_for_an_unknown_username(self):
        auth_service, user_repository = make_auth_service()
        user_repository.find_by_username.return_value = None

        self.assertIsNone(auth_service.login("nobody", "whatever"))

    def test_returns_none_for_the_wrong_password(self):
        auth_service, user_repository = make_auth_service()
        user_repository.find_by_username.return_value = make_stored_user("alice", "correct")

        self.assertIsNone(auth_service.login("alice", "wrong"))

    def test_returns_the_user_for_the_correct_password(self):
        auth_service, user_repository = make_auth_service()
        stored_user = make_stored_user("alice", "correct")
        user_repository.find_by_username.return_value = stored_user

        result = auth_service.login("alice", "correct")

        self.assertIs(result, stored_user)


class TestRegisterThenLoginEndToEndWithRealSqlite(unittest.TestCase):
    """No mocks: proves the whole hash-and-verify round trip through a real
    SqliteUserRepository, not just AuthService's own call arguments."""

    def test_correct_password_logs_in_after_registering(self):
        auth_service = AuthService(SqliteUserRepository(":memory:"))
        auth_service.register("alice", "hunter2")

        result = auth_service.login("alice", "hunter2")

        self.assertIsNotNone(result)
        self.assertEqual(result.username, "alice")
        self.assertEqual(result.rating, STARTING_RATING)

    def test_wrong_password_fails_to_log_in_after_registering(self):
        auth_service = AuthService(SqliteUserRepository(":memory:"))
        auth_service.register("alice", "hunter2")

        self.assertIsNone(auth_service.login("alice", "not-the-password"))

    def test_registering_the_same_username_twice_fails_the_second_time(self):
        auth_service = AuthService(SqliteUserRepository(":memory:"))
        auth_service.register("alice", "hunter2")

        self.assertIsNone(auth_service.register("alice", "different-password"))


if __name__ == "__main__":
    unittest.main()
