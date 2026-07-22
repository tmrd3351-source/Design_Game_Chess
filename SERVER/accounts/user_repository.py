from abc import ABC, abstractmethod


class User:

    def __init__(self, username, password_hash, rating):
        self.username = username
        self.password_hash = password_hash
        self.rating = rating


class UserRepository(ABC):
    """The contract AuthService depends on - swap the concrete
    implementation (SqliteUserRepository today, a Postgres one later)
    without touching AuthService at all."""

    @abstractmethod
    def find_by_username(self, username):
        """Returns the matching User, or None if no such user exists."""

    @abstractmethod
    def create_user(self, username, password_hash, rating):
        """Creates and returns a new User with the given fields."""

    @abstractmethod
    def update_rating(self, username, rating):
        """Persists a user's new rating."""
