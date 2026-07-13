import unittest

from model.move_result import MoveResult


class TestMoveResult(unittest.TestCase):

    def test_constructor_stores_valid_flag_and_reason(self):
        result = MoveResult(True, "legal")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.reason, "legal")

    def test_constructor_stores_false_and_reason(self):
        result = MoveResult(False, "blocked")
        self.assertFalse(result.is_valid)
        self.assertEqual(result.reason, "blocked")

    def test_constructor_accepts_none_reason(self):
        result = MoveResult(False, None)
        self.assertFalse(result.is_valid)
        self.assertIsNone(result.reason)

    def test_constructor_accepts_empty_string_reason(self):
        result = MoveResult(True, "")
        self.assertTrue(result.is_valid)
        self.assertEqual(result.reason, "")

    def test_legal_factory_returns_valid_result(self):
        result = MoveResult.legal()
        self.assertTrue(result.is_valid)
        self.assertEqual(result.reason, "legal")

    def test_legal_factory_returns_new_instance_each_call(self):
        first = MoveResult.legal()
        second = MoveResult.legal()
        self.assertIsNot(first, second)

    def test_illegal_factory_returns_invalid_result_with_given_reason(self):
        result = MoveResult.illegal("out_of_bounds")
        self.assertFalse(result.is_valid)
        self.assertEqual(result.reason, "out_of_bounds")

    def test_illegal_factory_preserves_arbitrary_reason_values(self):
        for reason in ["motion_in_progress", "game_over", "illegal_move", ""]:
            result = MoveResult.illegal(reason)
            self.assertFalse(result.is_valid)
            self.assertEqual(result.reason, reason)

    def test_illegal_factory_with_none_reason(self):
        result = MoveResult.illegal(None)
        self.assertFalse(result.is_valid)
        self.assertIsNone(result.reason)


if __name__ == "__main__":
    unittest.main()
