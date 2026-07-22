import unittest
from unittest.mock import Mock

from SERVER.session.session_ticker import SessionTicker


def make_ticker(sessions):
    game_manager = Mock()
    game_manager.sessions = sessions
    ticker = SessionTicker(game_manager)
    # Pin to a small, clean baseline - real time.time() is a huge float
    # (current epoch), and adding small deltas to it loses precision.
    ticker._last_tick = 0.0
    return ticker


class TestTick(unittest.TestCase):

    def test_advances_a_session_by_the_elapsed_milliseconds(self):
        session = Mock()
        ticker = make_ticker({"room-1": session})

        ticker.tick(now=ticker._last_tick + 0.5)  # 500ms later

        session.advance.assert_called_once_with(500)

    def test_ticks_every_active_session(self):
        session_a, session_b = Mock(), Mock()
        ticker = make_ticker({"a": session_a, "b": session_b})

        ticker.tick(now=ticker._last_tick + 1)

        session_a.advance.assert_called_once_with(1000)
        session_b.advance.assert_called_once_with(1000)

    def test_zero_elapsed_time_does_not_advance_any_session(self):
        session = Mock()
        ticker = make_ticker({"room-1": session})

        ticker.tick(now=ticker._last_tick)

        session.advance.assert_not_called()

    def test_negative_elapsed_time_does_not_advance_any_session(self):
        session = Mock()
        ticker = make_ticker({"room-1": session})

        ticker.tick(now=ticker._last_tick - 1)

        session.advance.assert_not_called()

    def test_second_tick_advances_only_by_time_since_the_previous_tick(self):
        session = Mock()
        ticker = make_ticker({"room-1": session})
        first_now = ticker._last_tick + 1

        ticker.tick(now=first_now)
        ticker.tick(now=first_now + 0.3)

        session.advance.assert_called_with(300)

    def test_no_sessions_is_a_no_op(self):
        ticker = make_ticker({})
        ticker.tick(now=ticker._last_tick + 1)  # must not raise


if __name__ == "__main__":
    unittest.main()
