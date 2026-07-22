import unittest

from CLIENT.gui.canvas import Canvas


class TestExtendRight(unittest.TestCase):

    def test_widens_the_image_by_the_requested_amount(self):
        canvas = Canvas.blank(100, 50)

        extended = canvas.extend_right(40)

        self.assertEqual(extended.img.shape[1], 140)
        self.assertEqual(extended.img.shape[0], 50)

    def test_keeps_the_same_channel_count(self):
        canvas = Canvas.blank(100, 50)

        extended = canvas.extend_right(40)

        self.assertEqual(extended.img.shape[2], canvas.img.shape[2])

    def test_original_image_is_untouched(self):
        canvas = Canvas.blank(100, 50)

        canvas.extend_right(40)

        self.assertEqual(canvas.img.shape[1], 100)

    def test_new_pixels_are_filled_with_the_requested_color(self):
        canvas = Canvas.blank(10, 10, color=(0, 0, 0))

        extended = canvas.extend_right(10, color=(1, 2, 3))

        appended_pixel = extended.img[0, 15]
        self.assertEqual(tuple(int(v) for v in appended_pixel[:3]), (1, 2, 3))


class TestDrawRoundedRect(unittest.TestCase):

    def test_fills_the_rects_flat_center_with_the_requested_color(self):
        canvas = Canvas.blank(100, 60, color=(0, 0, 0))

        canvas.draw_rounded_rect(10, 10, 80, 40, radius=12, color=(1, 2, 3))

        center_pixel = canvas.img[30, 50]
        self.assertEqual(tuple(int(v) for v in center_pixel), (1, 2, 3))

    def test_leaves_the_far_corner_untouched_by_the_rounded_cut(self):
        canvas = Canvas.blank(100, 60, color=(9, 9, 9))

        canvas.draw_rounded_rect(10, 10, 80, 40, radius=12, color=(1, 2, 3))

        corner_pixel = canvas.img[10, 10]
        self.assertEqual(tuple(int(v) for v in corner_pixel), (9, 9, 9))

    def test_outline_mode_leaves_the_interior_untouched(self):
        canvas = Canvas.blank(100, 60, color=(9, 9, 9))

        canvas.draw_rounded_rect(10, 10, 80, 40, radius=12, color=(1, 2, 3), thickness=2)

        center_pixel = canvas.img[30, 50]
        self.assertEqual(tuple(int(v) for v in center_pixel), (9, 9, 9))


if __name__ == "__main__":
    unittest.main()
