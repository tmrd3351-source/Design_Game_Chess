import unittest

from accounts.user_repository import User, UserRepository


class TestUser(unittest.TestCase):

    def test_stores_username_password_hash_and_rating(self):
        user = User("alice", "hash123", 1200)
        self.assertEqual(user.username, "alice")
        self.assertEqual(user.password_hash, "hash123")
        self.assertEqual(user.rating, 1200)


class TestUserRepositoryIsAbstract(unittest.TestCase):

    def test_cannot_be_instantiated_directly(self):
        with self.assertRaises(TypeError):
            UserRepository()

    def test_a_subclass_missing_a_method_still_cannot_be_instantiated(self):
        class IncompleteRepository(UserRepository):
            def find_by_username(self, username):
                return None

            def create_user(self, username, password_hash, rating):
                return None

            # update_rating deliberately not implemented

        with self.assertRaises(TypeError):
            IncompleteRepository()

    def test_a_subclass_implementing_every_method_can_be_instantiated(self):
        class CompleteRepository(UserRepository):
            def find_by_username(self, username):
                return None

            def create_user(self, username, password_hash, rating):
                return None

            def update_rating(self, username, rating):
                return None

        CompleteRepository()  # must not raise


if __name__ == "__main__":
    unittest.main()
