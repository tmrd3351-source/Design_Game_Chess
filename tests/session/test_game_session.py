import unittest
from unittest.mock import Mock

from session.game_session import GameSession, SPECTATOR
from events.event_bus import EventBus
from events.event_types import PLAYER_JOINED, GAME_STARTED, MOVE_COMPLETED, GAME_ENDED
from model.position import Position


def make_session(room_id="abc123"):
    controller = Mock()
    return GameSession(room_id, controller_factory=lambda: controller), controller


class TestGameSessionConstruction(unittest.TestCase):

    def test_stores_room_id(self):
        session, _ = make_session("room-1")
        self.assertEqual(session.room_id, "room-1")

    def test_builds_controller_via_the_factory(self):
        controller = Mock()
        session = GameSession("room-1", controller_factory=lambda: controller)
        self.assertIs(session.controller, controller)

    def test_starts_with_no_players_or_spectators(self):
        session, _ = make_session()
        self.assertEqual(session.players, {})
        self.assertEqual(session.spectators, [])

    def test_has_its_own_event_bus(self):
        session, _ = make_session()
        self.assertIsInstance(session.events, EventBus)

    def test_two_sessions_have_independent_event_buses(self):
        session_a, _ = make_session("room-a")
        session_b, _ = make_session("room-b")
        self.assertIsNot(session_a.events, session_b.events)


class TestJoin(unittest.TestCase):

    def test_first_joiner_becomes_white(self):
        session, _ = make_session()
        role = session.join("alice")
        self.assertEqual(role, "w")
        self.assertEqual(session.players["w"], "alice")

    def test_second_joiner_becomes_black(self):
        session, _ = make_session()
        session.join("alice")

        role = session.join("bob")

        self.assertEqual(role, "b")
        self.assertEqual(session.players["b"], "bob")

    def test_third_joiner_becomes_a_spectator(self):
        session, _ = make_session()
        session.join("alice")
        session.join("bob")

        role = session.join("carol")

        self.assertEqual(role, SPECTATOR)
        self.assertEqual(session.spectators, ["carol"])

    def test_further_joiners_are_all_spectators_in_order(self):
        session, _ = make_session()
        session.join("alice")
        session.join("bob")
        session.join("carol")
        session.join("dave")

        self.assertEqual(session.spectators, ["carol", "dave"])

    def test_white_and_black_slots_are_not_reassigned_once_taken(self):
        session, _ = make_session()
        session.join("alice")
        session.join("bob")

        self.assertEqual(session.players, {"w": "alice", "b": "bob"})


class TestJoinPublishesEvents(unittest.TestCase):

    def test_every_joiner_publishes_player_joined_with_their_name_and_role(self):
        session, _ = make_session()
        received = []
        session.events.subscribe(PLAYER_JOINED, lambda **payload: received.append(payload))

        session.join("alice")
        session.join("bob")
        session.join("carol")

        self.assertEqual(received, [
            {"name": "alice", "role": "w"},
            {"name": "bob", "role": "b"},
            {"name": "carol", "role": SPECTATOR},
        ])

    def test_game_started_is_not_published_until_black_joins(self):
        session, _ = make_session()
        callback = Mock()
        session.events.subscribe(GAME_STARTED, callback)

        session.join("alice")

        callback.assert_not_called()

    def test_game_started_is_published_once_black_joins(self):
        session, _ = make_session("room-42")
        callback = Mock()
        session.events.subscribe(GAME_STARTED, callback)

        session.join("alice")
        session.join("bob")

        callback.assert_called_once_with(room_id="room-42")

    def test_game_started_is_not_published_again_for_spectators(self):
        session, _ = make_session()
        callback = Mock()
        session.join("alice")
        session.join("bob")
        session.events.subscribe(GAME_STARTED, callback)

        session.join("carol")

        callback.assert_not_called()


class TestAdvance(unittest.TestCase):

    def test_delegates_to_controller_handle_wait_with_elapsed_ms(self):
        session, controller = make_session()
        controller.game_engine.arbiter.motions = []
        controller.get_state.return_value = Mock(motions=[], game_over=False)

        session.advance(500)

        controller.handle_wait.assert_called_once_with(500)

    def test_does_not_publish_move_completed_when_nothing_was_pending(self):
        session, controller = make_session()
        controller.game_engine.arbiter.motions = []
        controller.get_state.return_value = Mock(motions=[], game_over=False)
        callback = Mock()
        session.events.subscribe(MOVE_COMPLETED, callback)

        session.advance(500)

        callback.assert_not_called()

    def test_does_not_publish_move_completed_while_a_motion_is_still_pending(self):
        session, controller = make_session()
        still_pending = Mock()
        controller.game_engine.arbiter.motions = [still_pending]
        controller.get_state.return_value = Mock(motions=[still_pending], game_over=False)
        callback = Mock()
        session.events.subscribe(MOVE_COMPLETED, callback)

        session.advance(500)

        callback.assert_not_called()

    def test_publishes_move_completed_once_a_pending_motion_is_gone(self):
        session, controller = make_session()
        landed = Mock()
        controller.game_engine.arbiter.motions = [landed]
        new_state = Mock(motions=[], game_over=False)
        controller.get_state.return_value = new_state
        callback = Mock()
        session.events.subscribe(MOVE_COMPLETED, callback)

        session.advance(500)

        callback.assert_called_once_with(room_id=session.room_id, state=new_state)

    def test_does_not_publish_game_ended_while_game_over_stays_false(self):
        session, controller = make_session()
        controller.game_engine.arbiter.motions = []
        controller.game_engine.arbiter.game_over = False
        controller.get_state.return_value = Mock(motions=[], game_over=False)
        callback = Mock()
        session.events.subscribe(GAME_ENDED, callback)

        session.advance(500)

        callback.assert_not_called()

    def test_publishes_game_ended_when_game_over_flips_to_true(self):
        session, controller = make_session()
        session.players = {"w": "alice", "b": "bob"}
        controller.game_engine.arbiter.motions = []
        controller.game_engine.arbiter.game_over = False
        controller.get_state.return_value = Mock(motions=[], game_over=True, winner="w")
        callback = Mock()
        session.events.subscribe(GAME_ENDED, callback)

        session.advance(500)

        callback.assert_called_once_with(room_id=session.room_id, winner="w",
                                          players={"w": "alice", "b": "bob"})

    def test_does_not_republish_game_ended_once_already_over(self):
        session, controller = make_session()
        controller.game_engine.arbiter.motions = []
        controller.game_engine.arbiter.game_over = True  # already ended before this tick
        controller.get_state.return_value = Mock(motions=[], game_over=True, winner="w")
        callback = Mock()
        session.events.subscribe(GAME_ENDED, callback)

        session.advance(500)

        callback.assert_not_called()


class TestAdvanceEndToEndWithRealController(unittest.TestCase):
    """No mocks: schedules a real capturing move through the real Controller/
    GameEngine, then proves advance() detects both the landing and the
    game_over transition, publishing MOVE_COMPLETED and GAME_ENDED for real."""

    def test_a_scheduled_capture_publishes_move_completed_and_game_ended_once_it_lands(self):
        session = GameSession("room-1")
        session.players = {"w": "alice", "b": "bob"}

        board = session.controller.game_engine.board
        white_king = board.get_piece(Position(7, 4))
        board.remove_piece(Position(7, 4))
        white_king.set_position(Position(1, 4))
        board.add_piece(white_king)
        session.controller.handle_move(Position(1, 4), Position(0, 4))

        move_completed = []
        game_ended = []
        session.events.subscribe(MOVE_COMPLETED, lambda **payload: move_completed.append(payload))
        session.events.subscribe(GAME_ENDED, lambda **payload: game_ended.append(payload))

        session.advance(1000)  # long enough for the capture to land

        self.assertEqual(len(move_completed), 1)
        self.assertEqual(len(game_ended), 1)
        self.assertEqual(game_ended[0]["winner"], "w")
        self.assertEqual(game_ended[0]["players"], {"w": "alice", "b": "bob"})


if __name__ == "__main__":
    unittest.main()
