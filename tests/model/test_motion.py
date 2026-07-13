import unittest
from unittest.mock import Mock

from model.motion import Motion


class TestMotionConstruction(unittest.TestCase):

    def test_stores_required_fields(self):
        piece = Mock()
        origin = Mock()
        source = Mock()
        destination = Mock()
        motion = Motion(piece, origin, source, destination, start_time=100, duration=1000)

        self.assertIs(motion.piece, piece)
        self.assertIs(motion.origin, origin)
        self.assertIs(motion.source, source)
        self.assertIs(motion.destination, destination)
        self.assertEqual(motion.start_time, 100)
        self.assertEqual(motion.duration, 1000)

    def test_default_kind_is_translate(self):
        motion = Motion(Mock(), Mock(), Mock(), Mock(), 0, 1000)
        self.assertEqual(motion.kind, "translate")

    def test_kind_can_be_overridden_to_jump(self):
        motion = Motion(Mock(), Mock(), Mock(), Mock(), 0, 1000, kind="jump")
        self.assertEqual(motion.kind, "jump")

    def test_default_sequence_is_zero(self):
        motion = Motion(Mock(), Mock(), Mock(), Mock(), 0, 1000)
        self.assertEqual(motion.sequence, 0)

    def test_sequence_can_be_overridden(self):
        motion = Motion(Mock(), Mock(), Mock(), Mock(), 0, 1000, sequence=42)
        self.assertEqual(motion.sequence, 42)

    def test_remaining_route_defaults_to_empty_list_when_none(self):
        motion = Motion(Mock(), Mock(), Mock(), Mock(), 0, 1000, remaining_route=None)
        self.assertEqual(motion.remaining_route, [])

    def test_remaining_route_defaults_to_empty_list_when_omitted(self):
        motion = Motion(Mock(), Mock(), Mock(), Mock(), 0, 1000)
        self.assertEqual(motion.remaining_route, [])

    def test_remaining_route_with_explicit_empty_list_is_not_preserved_by_identity(self):
        # `remaining_route or []` treats an explicitly empty list the same
        # as None: it is falsy, so a *new* empty list is stored instead of
        # the caller's own list instance.
        route = []
        motion = Motion(Mock(), Mock(), Mock(), Mock(), 0, 1000, remaining_route=route)
        self.assertEqual(motion.remaining_route, [])
        self.assertIsNot(motion.remaining_route, route)

    def test_remaining_route_preserves_explicit_non_empty_list(self):
        step_a = Mock()
        step_b = Mock()
        motion = Motion(Mock(), Mock(), Mock(), Mock(), 0, 1000, remaining_route=[step_a, step_b])
        self.assertEqual(motion.remaining_route, [step_a, step_b])

    def test_progress_starts_at_zero(self):
        motion = Motion(Mock(), Mock(), Mock(), Mock(), 0, 1000)
        self.assertEqual(motion.progress, 0.0)


class TestMotionUpdate(unittest.TestCase):

    def test_update_at_start_time_gives_zero_progress(self):
        motion = Motion(Mock(), Mock(), Mock(), Mock(), start_time=1000, duration=1000)
        motion.update(1000)
        self.assertEqual(motion.progress, 0.0)

    def test_update_halfway_gives_half_progress(self):
        motion = Motion(Mock(), Mock(), Mock(), Mock(), start_time=0, duration=1000)
        motion.update(500)
        self.assertAlmostEqual(motion.progress, 0.5)

    def test_update_at_exact_duration_gives_full_progress(self):
        motion = Motion(Mock(), Mock(), Mock(), Mock(), start_time=0, duration=1000)
        motion.update(1000)
        self.assertEqual(motion.progress, 1.0)

    def test_update_past_duration_is_clamped_to_one(self):
        motion = Motion(Mock(), Mock(), Mock(), Mock(), start_time=0, duration=1000)
        motion.update(5000)
        self.assertEqual(motion.progress, 1.0)

    def test_update_before_start_time_is_clamped_to_zero(self):
        motion = Motion(Mock(), Mock(), Mock(), Mock(), start_time=1000, duration=1000)
        motion.update(0)
        self.assertEqual(motion.progress, 0.0)

    def test_update_with_zero_duration_raises_zero_division_error(self):
        motion = Motion(Mock(), Mock(), Mock(), Mock(), start_time=0, duration=0)
        with self.assertRaises(ZeroDivisionError):
            motion.update(0)

    def test_multiple_updates_move_progress_forward(self):
        motion = Motion(Mock(), Mock(), Mock(), Mock(), start_time=0, duration=1000)
        motion.update(250)
        self.assertAlmostEqual(motion.progress, 0.25)
        motion.update(750)
        self.assertAlmostEqual(motion.progress, 0.75)


class TestMotionIsComplete(unittest.TestCase):

    def test_is_complete_false_before_any_update(self):
        motion = Motion(Mock(), Mock(), Mock(), Mock(), start_time=0, duration=1000)
        self.assertFalse(motion.is_complete())

    def test_is_complete_false_when_progress_below_one(self):
        motion = Motion(Mock(), Mock(), Mock(), Mock(), start_time=0, duration=1000)
        motion.update(999)
        self.assertFalse(motion.is_complete())

    def test_is_complete_true_when_progress_exactly_one(self):
        motion = Motion(Mock(), Mock(), Mock(), Mock(), start_time=0, duration=1000)
        motion.update(1000)
        self.assertTrue(motion.is_complete())

    def test_is_complete_true_when_progress_beyond_one(self):
        motion = Motion(Mock(), Mock(), Mock(), Mock(), start_time=0, duration=1000)
        motion.update(9999)
        self.assertTrue(motion.is_complete())


if __name__ == "__main__":
    unittest.main()
