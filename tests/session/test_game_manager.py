import unittest
from unittest.mock import Mock

from session.game_manager import GameManager


class TestCreateSession(unittest.TestCase):

    def test_returns_a_session_built_by_the_factory(self):
        session = Mock()
        manager = GameManager(session_factory=lambda room_id: session)

        created = manager.create_session()

        self.assertIs(created, session)

    def test_passes_the_generated_room_id_to_the_factory(self):
        manager = GameManager(session_factory=lambda room_id: Mock(room_id=room_id))

        created = manager.create_session()

        self.assertIsNotNone(created.room_id)

    def test_registers_the_session_under_its_room_id(self):
        manager = GameManager(session_factory=lambda room_id: Mock(room_id=room_id))

        created = manager.create_session()

        self.assertIs(manager.sessions[created.room_id], created)

    def test_successive_sessions_get_different_room_ids(self):
        manager = GameManager(session_factory=lambda room_id: Mock(room_id=room_id))

        first = manager.create_session()
        second = manager.create_session()

        self.assertNotEqual(first.room_id, second.room_id)

    def test_default_session_factory_is_the_real_game_session_class(self):
        manager = GameManager()
        self.assertEqual(manager._session_factory.__name__, "GameSession")


class TestJoinSession(unittest.TestCase):

    def test_returns_the_session_registered_under_that_room_id(self):
        manager = GameManager(session_factory=lambda room_id: Mock(room_id=room_id))
        created = manager.create_session()

        self.assertIs(manager.join_session(created.room_id), created)

    def test_returns_none_for_an_unknown_room_id(self):
        manager = GameManager()
        self.assertIsNone(manager.join_session("no-such-room"))


if __name__ == "__main__":
    unittest.main()
