import hashlib
import secrets

STARTING_RATING = 1200
_HASH_ITERATIONS = 100_000


def _hash_password(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), _HASH_ITERATIONS).hex()


class AuthService:
    """Registration and login - only ever talks to UserRepository, never a
    concrete database. Passwords are salted and hashed before they ever
    reach the repository; nothing downstream sees the plaintext."""

    def __init__(self, user_repository):
        self.user_repository = user_repository

    def get_user(self, username):
        return self.user_repository.find_by_username(username)

    def register(self, username, password):
        if self.user_repository.find_by_username(username) is not None:
            return None

        salt = secrets.token_hex(16)
        password_hash = f"{salt}:{_hash_password(password, salt)}"
        return self.user_repository.create_user(username, password_hash, STARTING_RATING)

    def login(self, username, password):
        user = self.user_repository.find_by_username(username)
        if user is None:
            return None

        salt, _, expected_hash = user.password_hash.partition(":")
        if _hash_password(password, salt) != expected_hash:
            return None

        return user
