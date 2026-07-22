import sqlite3

from SERVER.accounts.user_repository import UserRepository, User


class SqliteUserRepository(UserRepository):
    """UserRepository backed by SQLite. Holds one open connection for the
    life of the instance, so `db_path=":memory:"` also works for tests -
    a fresh connection per call would otherwise get a brand new, empty
    in-memory database every time."""

    def __init__(self, db_path):
        self._connection = sqlite3.connect(db_path)
        self._connection.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                rating INTEGER NOT NULL
            )
        """)
        self._connection.commit()

    def find_by_username(self, username):
        row = self._connection.execute(
            "SELECT username, password_hash, rating FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        return User(*row) if row else None

    def create_user(self, username, password_hash, rating):
        self._connection.execute(
            "INSERT INTO users (username, password_hash, rating) VALUES (?, ?, ?)",
            (username, password_hash, rating),
        )
        self._connection.commit()
        return User(username, password_hash, rating)

    def update_rating(self, username, rating):
        self._connection.execute(
            "UPDATE users SET rating = ? WHERE username = ?",
            (rating, username),
        )
        self._connection.commit()
