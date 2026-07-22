import unittest
from unittest.mock import Mock

from SERVER.session.game_session import GameSession, SPECTATOR
from SERVER.events.event_bus import EventBus
from SERVER.events.event_types import (
    PLAYER_JOINED, GAME_STARTED, MOVE_COMPLETED, GAME_ENDED,
    PLAYER_DISCONNECTED, PLAYER_RECONNECTED,
)
from SERVER.model.position import Position


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

    def test_rejoining_an_already_seated_player_returns_their_existing_role(self):
        session, _ = make_session()
        session.join("alice")
        session.join("bob")

        role = session.join("alice")

        self.assertEqual(role, "w")

    def test_rejoining_an_already_seated_player_does_not_demote_them_to_spectator(self):
        # Before the reconnect-safe join(), a full room would push a
        # returning player into spectators instead of recognizing them.
        session, _ = make_session()
        session.join("alice")
        session.join("bob")

        session.join("alice")

        self.assertEqual(session.players, {"w": "alice", "b": "bob"})
        self.assertEqual(session.spectators, [])

    def test_rejoining_does_not_republish_player_joined(self):
        session, _ = make_session()
        session.join("alice")
        session.join("bob")
        callback = Mock()
        session.events.subscribe(PLAYER_JOINED, callback)

        session.join("alice")

        callback.assert_not_called()

    def test_rejoining_clears_the_pending_disconnect(self):
        session, _ = make_session()
        session.join("alice")
        session.join("bob")
        session.mark_disconnected("alice")

        session.join("alice")

        self.assertNotIn("alice", session.pending_disconnects)


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


class TestColorOf(unittest.TestCase):

    def test_returns_the_seated_players_color(self):
        session, _ = make_session()
        session.join("alice")
        session.join("bob")

        self.assertEqual(session.color_of("alice"), "w")
        self.assertEqual(session.color_of("bob"), "b")

    def test_returns_none_for_a_spectator(self):
        session, _ = make_session()
        session.join("alice")
        session.join("bob")
        session.join("carol")

        self.assertIsNone(session.color_of("carol"))

    def test_returns_none_for_an_unknown_username(self):
        session, _ = make_session()
        session.join("alice")

        self.assertIsNone(session.color_of("nobody"))


class TestMarkDisconnected(unittest.TestCase):

    def test_adds_a_seated_player_to_pending_disconnects(self):
        session, _ = make_session()
        session.join("alice")

        session.mark_disconnected("alice")

        self.assertIn("alice", session.pending_disconnects)

    def test_publishes_player_disconnected_with_room_id_and_name(self):
        session, _ = make_session("room-1")
        session.join("alice")
        callback = Mock()
        session.events.subscribe(PLAYER_DISCONNECTED, callback)

        session.mark_disconnected("alice")

        callback.assert_called_once_with(room_id="room-1", name="alice")

    def test_a_spectator_or_unknown_username_is_never_tracked(self):
        session, _ = make_session()
        session.join("alice")
        session.join("bob")
        session.join("carol")  # spectator
        callback = Mock()
        session.events.subscribe(PLAYER_DISCONNECTED, callback)

        session.mark_disconnected("carol")
        session.mark_disconnected("nobody")

        self.assertEqual(session.pending_disconnects, set())
        callback.assert_not_called()


class TestMarkReconnected(unittest.TestCase):

    def test_removes_from_pending_disconnects(self):
        session, _ = make_session()
        session.join("alice")
        session.mark_disconnected("alice")

        session.mark_reconnected("alice")

        self.assertNotIn("alice", session.pending_disconnects)

    def test_publishes_player_reconnected_with_room_id_and_name(self):
        session, _ = make_session("room-1")
        session.join("alice")
        session.mark_disconnected("alice")
        callback = Mock()
        session.events.subscribe(PLAYER_RECONNECTED, callback)

        session.mark_reconnected("alice")

        callback.assert_called_once_with(room_id="room-1", name="alice")

    def test_reconnecting_someone_who_was_never_disconnected_does_nothing(self):
        session, _ = make_session()
        session.join("alice")
        callback = Mock()
        session.events.subscribe(PLAYER_RECONNECTED, callback)

        session.mark_reconnected("alice")

        callback.assert_not_called()


class TestIsReconnectable(unittest.TestCase):

    def test_true_while_pending_and_game_not_over(self):
        session, controller = make_session()
        controller.game_engine.arbiter.game_over = False
        session.join("alice")
        session.mark_disconnected("alice")

        self.assertTrue(session.is_reconnectable("alice"))

    def test_false_when_never_disconnected(self):
        session, controller = make_session()
        controller.game_engine.arbiter.game_over = False
        session.join("alice")

        self.assertFalse(session.is_reconnectable("alice"))

    def test_false_once_the_game_is_already_over(self):
        session, controller = make_session()
        session.join("alice")
        session.mark_disconnected("alice")
        controller.game_engine.arbiter.game_over = True

        self.assertFalse(session.is_reconnectable("alice"))


class TestForfeitByDisconnect(unittest.TestCase):

    def test_the_other_seated_player_is_declared_the_winner(self):
        session, controller = make_session()
        controller.game_engine.arbiter.game_over = False
        session.join("alice")
        session.join("bob")
        session.mark_disconnected("alice")

        session.forfeit_by_disconnect("alice")

        self.assertTrue(controller.game_engine.arbiter.game_over)
        self.assertEqual(controller.game_engine.arbiter.winner, "b")

    def test_publishes_game_ended_with_the_same_shape_as_a_real_win(self):
        session, controller = make_session("room-1")
        controller.game_engine.arbiter.game_over = False
        session.join("alice")
        session.join("bob")
        session.mark_disconnected("bob")
        callback = Mock()
        session.events.subscribe(GAME_ENDED, callback)

        session.forfeit_by_disconnect("bob")

        callback.assert_called_once_with(room_id="room-1", winner="w",
                                          players={"w": "alice", "b": "bob"})

    def test_clears_the_pending_disconnect(self):
        session, controller = make_session()
        controller.game_engine.arbiter.game_over = False
        session.join("alice")
        session.join("bob")
        session.mark_disconnected("alice")

        session.forfeit_by_disconnect("alice")

        self.assertNotIn("alice", session.pending_disconnects)

    def test_does_nothing_if_the_game_already_ended_for_a_real_reason(self):
        session, controller = make_session()
        session.join("alice")
        session.join("bob")
        session.mark_disconnected("alice")
        controller.game_engine.arbiter.game_over = True
        controller.game_engine.arbiter.winner = "w"  # a real king-capture win

        session.forfeit_by_disconnect("alice")

        # Untouched - not overwritten with a forfeit result.
        self.assertEqual(controller.game_engine.arbiter.winner, "w")


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
