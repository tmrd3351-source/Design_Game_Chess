import unittest
from unittest.mock import Mock

from SHARED.model.cooldown import Cooldown


class TestCooldownConstruction(unittest.TestCase):

    def test_stores_required_fields(self):
        piece = Mock()
        position = Mock()
        cooldown = Cooldown(piece, position, start_time=100, duration=500)

        self.assertIs(cooldown.piece, piece)
        self.assertIs(cooldown.position, position)
        self.assertEqual(cooldown.start_time, 100)
        self.assertEqual(cooldown.duration, 500)

    def test_progress_starts_at_zero(self):
        cooldown = Cooldown(Mock(), Mock(), 0, 500)
        self.assertEqual(cooldown.progress, 0.0)


class TestCooldownUpdate(unittest.TestCase):

    def test_update_at_start_time_gives_zero_progress(self):
        cooldown = Cooldown(Mock(), Mock(), start_time=1000, duration=500)
        cooldown.update(1000)
        self.assertEqual(cooldown.progress, 0.0)

    def test_update_halfway_gives_half_progress(self):
        cooldown = Cooldown(Mock(), Mock(), start_time=0, duration=500)
        cooldown.update(250)
        self.assertAlmostEqual(cooldown.progress, 0.5)

    def test_update_at_exact_duration_gives_full_progress(self):
        cooldown = Cooldown(Mock(), Mock(), start_time=0, duration=500)
        cooldown.update(500)
        self.assertEqual(cooldown.progress, 1.0)

    def test_update_past_duration_is_clamped_to_one(self):
        cooldown = Cooldown(Mock(), Mock(), start_time=0, duration=500)
        cooldown.update(5000)
        self.assertEqual(cooldown.progress, 1.0)

    def test_update_before_start_time_is_clamped_to_zero(self):
        cooldown = Cooldown(Mock(), Mock(), start_time=1000, duration=500)
        cooldown.update(0)
        self.assertEqual(cooldown.progress, 0.0)


class TestCooldownIsComplete(unittest.TestCase):

    def test_is_complete_false_before_any_update(self):
        cooldown = Cooldown(Mock(), Mock(), start_time=0, duration=500)
        self.assertFalse(cooldown.is_complete())

    def test_is_complete_true_when_progress_exactly_one(self):
        cooldown = Cooldown(Mock(), Mock(), start_time=0, duration=500)
        cooldown.update(500)
        self.assertTrue(cooldown.is_complete())


if __name__ == "__main__":
    unittest.main()
