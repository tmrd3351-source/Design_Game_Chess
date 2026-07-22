import unittest

from SERVER.accounts.sqlite_user_repository import SqliteUserRepository
from SERVER.accounts.user_repository import User


def make_repository():
    return SqliteUserRepository(":memory:")


class TestFindByUsername(unittest.TestCase):

    def test_returns_none_for_an_unknown_username(self):
        repository = make_repository()
        self.assertIsNone(repository.find_by_username("nobody"))

    def test_returns_the_stored_user_after_creation(self):
        repository = make_repository()
        repository.create_user("alice", "hash123", 1200)

        found = repository.find_by_username("alice")

        self.assertIsInstance(found, User)
        self.assertEqual(found.username, "alice")
        self.assertEqual(found.password_hash, "hash123")
        self.assertEqual(found.rating, 1200)


class TestCreateUser(unittest.TestCase):

    def test_returns_a_user_with_the_given_fields(self):
        repository = make_repository()
        created = repository.create_user("bob", "hash456", 1200)

        self.assertEqual(created.username, "bob")
        self.assertEqual(created.password_hash, "hash456")
        self.assertEqual(created.rating, 1200)

    def test_duplicate_username_raises(self):
        repository = make_repository()
        repository.create_user("alice", "hash123", 1200)

        with self.assertRaises(Exception):
            repository.create_user("alice", "hash999", 1200)

    def test_persists_across_repeated_lookups(self):
        repository = make_repository()
        repository.create_user("alice", "hash123", 1200)

        self.assertIsNotNone(repository.find_by_username("alice"))
        self.assertIsNotNone(repository.find_by_username("alice"))


class TestUpdateRating(unittest.TestCase):

    def test_changes_the_stored_rating(self):
        repository = make_repository()
        repository.create_user("alice", "hash123", 1200)

        repository.update_rating("alice", 1214)

        self.assertEqual(repository.find_by_username("alice").rating, 1214)

    def test_does_not_touch_username_or_password_hash(self):
        repository = make_repository()
        repository.create_user("alice", "hash123", 1200)

        repository.update_rating("alice", 1214)

        found = repository.find_by_username("alice")
        self.assertEqual(found.username, "alice")
        self.assertEqual(found.password_hash, "hash123")

    def test_unknown_username_is_a_no_op(self):
        repository = make_repository()
        repository.update_rating("nobody", 1300)  # must not raise
        self.assertIsNone(repository.find_by_username("nobody"))


class TestTwoRepositoryInstancesAreIndependent(unittest.TestCase):

    def test_separate_in_memory_databases_do_not_share_users(self):
        repository_a = make_repository()
        repository_b = make_repository()

        repository_a.create_user("alice", "hash123", 1200)

        self.assertIsNone(repository_b.find_by_username("alice"))


if __name__ == "__main__":
    unittest.main()
