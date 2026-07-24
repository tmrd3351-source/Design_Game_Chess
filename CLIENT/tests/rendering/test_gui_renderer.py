import unittest
from unittest.mock import Mock

from CLIENT.rendering.gui_renderer import GuiRenderer
from CLIENT.config.constants import REST_LONG, REST_NONE
from CLIENT.model.position import Position


def make_piece(color, rest_type=REST_LONG):
    piece = Mock()
    piece.get_color.return_value = color
    piece.get_rest_type.return_value = rest_type
    piece.get_rest_progress.return_value = 0.5
    return piece


class FakeBoard:
    """A 1x1 board holding a single piece at (0, 0) - just enough for
    draw_cooldown to iterate without touching the real Board/Position."""

    def __init__(self, piece):
        self.rows = 1
        self.cols = 1
        self._piece = piece

    def get_piece(self, position):
        if position.get_row() == 0 and position.get_col() == 0:
            return self._piece
        return None


class TestDrawCooldown(unittest.TestCase):

    def test_draws_the_overlay_when_no_color_filter_is_given(self):
        canvas = Mock()
        board = FakeBoard(make_piece("w"))

        GuiRenderer().draw_cooldown(canvas, board, my_color=None)

        canvas.draw_overlay_rect.assert_called_once()

    def test_draws_a_piece_matching_my_color(self):
        canvas = Mock()
        board = FakeBoard(make_piece("w"))

        GuiRenderer().draw_cooldown(canvas, board, my_color="w")

        canvas.draw_overlay_rect.assert_called_once()

    def test_hides_a_piece_belonging_to_the_opponent(self):
        canvas = Mock()
        board = FakeBoard(make_piece("b"))

        GuiRenderer().draw_cooldown(canvas, board, my_color="w")

        canvas.draw_overlay_rect.assert_not_called()

    def test_a_piece_with_no_active_rest_is_never_drawn_regardless_of_color(self):
        canvas = Mock()
        board = FakeBoard(make_piece("w", rest_type=REST_NONE))

        GuiRenderer().draw_cooldown(canvas, board, my_color="w")

        canvas.draw_overlay_rect.assert_not_called()


def make_move(color="w", kind="R", source=(6, 0), destination=(5, 0), captured=None):
    return {
        "color": color, "kind": kind,
        "source": Position(*source), "destination": Position(*destination),
        "captured": captured or [],
    }


def texts_drawn(canvas):
    return [call.args[0] for call in canvas.put_text.call_args_list]


class TestDrawScorePanel(unittest.TestCase):

    def test_draws_both_colors_scores(self):
        canvas = Mock()
        game_state = Mock(score={"w": 5, "b": 2}, move_log=[])

        GuiRenderer().draw_score_panel(canvas, game_state)

        texts = texts_drawn(canvas)
        self.assertTrue(any("White" in t and "5" in t for t in texts))
        self.assertTrue(any("Black" in t and "2" in t for t in texts))

    def test_draws_a_line_per_move_including_the_capture(self):
        canvas = Mock()
        game_state = Mock(score={"w": 0, "b": 0}, move_log=[make_move(captured=["P"])])

        GuiRenderer().draw_score_panel(canvas, game_state)

        texts = texts_drawn(canvas)
        self.assertTrue(any("White" in t and "R" in t and "xP" in t for t in texts))

    def test_a_move_with_no_capture_has_no_x_suffix(self):
        canvas = Mock()
        game_state = Mock(score={"w": 0, "b": 0}, move_log=[make_move(captured=[])])

        GuiRenderer().draw_score_panel(canvas, game_state)

        move_lines = [t for t in texts_drawn(canvas) if "->" in t]
        self.assertEqual(len(move_lines), 1)
        self.assertNotIn("x", move_lines[0].split("->")[1])

    def test_a_jump_entry_is_labeled_as_a_jump_instead_of_an_arrow_to_itself(self):
        canvas = Mock()
        jump_entry = make_move(kind="K", source=(1, 1), destination=(1, 1))
        game_state = Mock(score={"w": 0, "b": 0}, move_log=[jump_entry])

        GuiRenderer().draw_score_panel(canvas, game_state)

        texts = texts_drawn(canvas)
        self.assertTrue(any("jump" in t and "(1,1)" in t for t in texts))
        self.assertFalse(any("->" in t for t in texts))

    def test_only_the_most_recent_moves_are_shown(self):
        canvas = Mock()
        from CLIENT.rendering.gui_renderer import PANEL_MAX_MOVES_SHOWN
        move_log = [make_move() for _ in range(PANEL_MAX_MOVES_SHOWN + 5)]
        game_state = Mock(score={"w": 0, "b": 0}, move_log=move_log)

        GuiRenderer().draw_score_panel(canvas, game_state)

        move_lines = [t for t in texts_drawn(canvas) if "->" in t]
        self.assertEqual(len(move_lines), PANEL_MAX_MOVES_SHOWN)

    def test_no_moves_yet_draws_only_the_headers(self):
        canvas = Mock()
        game_state = Mock(score={"w": 0, "b": 0}, move_log=[])

        GuiRenderer().draw_score_panel(canvas, game_state)

        move_lines = [t for t in texts_drawn(canvas) if "->" in t]
        self.assertEqual(move_lines, [])


if __name__ == "__main__":
    unittest.main()
