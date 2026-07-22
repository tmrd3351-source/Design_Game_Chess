import asyncio

from SERVER.accounts.auth_service import AuthService
from SERVER.accounts.sqlite_user_repository import SqliteUserRepository
from SERVER.session.game_manager import GameManager
from SERVER.session.matchmaker import Matchmaker
from SERVER.session.session_ticker import SessionTicker
from SERVER.network.connection_router import ConnectionRouter
from SERVER.network.websocket_server import WebSocketServer

DB_PATH = "users.db"


def build_server(host="localhost", port=8765):
    """Composition root for the server process - the network/session-layer
    counterpart to app.py's Application for the local GUI/CLI process."""
    user_repository = SqliteUserRepository(DB_PATH)
    auth_service = AuthService(user_repository)
    game_manager = GameManager()
    matchmaker = Matchmaker(game_manager)
    connection_router = ConnectionRouter(game_manager, auth_service, matchmaker)
    session_ticker = SessionTicker(game_manager)
    return WebSocketServer(connection_router, game_manager, session_ticker, host, port)


if __name__ == "__main__":
    print("Starting server...")

    asyncio.run(build_server().start())
