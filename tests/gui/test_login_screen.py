import unittest
from unittest.mock import Mock

from gui.login_screen import LoginScreen, TAB_KEY, BACKSPACE_KEY, ENTER_KEY
from network.protocol import LoginSucceeded, LoginFailed


def make_screen(login_fn=None):
    return LoginScreen(server_uri="ws://unused", login_fn=login_fn or Mock())


class TestConstruction(unittest.TestCase):

    def test_starts_with_empty_fields_and_username_active(self):
        screen = make_screen()
        self.assertEqual(screen.username, "")
        self.assertEqual(screen.password, "")
        self.assertEqual(screen.active_field, "username")
        self.assertEqual(screen.message, "")
        self.assertIsNone(screen.logged_in_username)


class TestTypingAndFieldSwitching(unittest.TestCase):

    def test_typed_characters_go_to_the_active_field(self):
        screen = make_screen()
        for char in "alice":
            screen.handle_key(ord(char))
        self.assertEqual(screen.username, "alice")
        self.assertEqual(screen.password, "")

    def test_tab_switches_the_active_field(self):
        screen = make_screen()
        screen.handle_key(TAB_KEY)
        self.assertEqual(screen.active_field, "password")
        screen.handle_key(TAB_KEY)
        self.assertEqual(screen.active_field, "username")

    def test_typed_characters_after_tab_go_to_password(self):
        screen = make_screen()
        screen.handle_key(TAB_KEY)
        for char in "hunter2":
            screen.handle_key(ord(char))
        self.assertEqual(screen.password, "hunter2")
        self.assertEqual(screen.username, "")

    def test_backspace_removes_the_last_character_of_the_active_field(self):
        screen = make_screen()
        for char in "alice":
            screen.handle_key(ord(char))
        screen.handle_key(BACKSPACE_KEY)
        self.assertEqual(screen.username, "alic")

    def test_backspace_on_empty_field_is_a_no_op(self):
        screen = make_screen()
        screen.handle_key(BACKSPACE_KEY)
        self.assertEqual(screen.username, "")

    def test_handle_key_returns_false_for_non_submitting_keys(self):
        screen = make_screen()
        self.assertFalse(screen.handle_key(ord("a")))
        self.assertFalse(screen.handle_key(TAB_KEY))
        self.assertFalse(screen.handle_key(BACKSPACE_KEY))


class TestSubmit(unittest.TestCase):

    def test_empty_username_is_rejected_without_calling_login_fn(self):
        login_fn = Mock()
        screen = make_screen(login_fn)
        screen.handle_key(TAB_KEY)
        for char in "hunter2":
            screen.handle_key(ord(char))

        result = screen.submit()

        self.assertFalse(result)
        login_fn.assert_not_called()
        self.assertTrue(screen.failed_last_attempt)

    def test_empty_password_is_rejected_without_calling_login_fn(self):
        login_fn = Mock()
        screen = make_screen(login_fn)
        for char in "alice":
            screen.handle_key(ord(char))

        result = screen.submit()

        self.assertFalse(result)
        login_fn.assert_not_called()

    def test_calls_login_fn_with_the_typed_username_and_password(self):
        login_fn = Mock(return_value=LoginSucceeded("alice"))
        screen = make_screen(login_fn)
        for char in "alice":
            screen.handle_key(ord(char))
        screen.handle_key(TAB_KEY)
        for char in "hunter2":
            screen.handle_key(ord(char))

        screen.submit()

        login_fn.assert_called_once_with("alice", "hunter2")

    def test_success_response_returns_true_and_stores_the_username(self):
        login_fn = Mock(return_value=LoginSucceeded("alice"))
        screen = make_screen(login_fn)
        screen.username, screen.password = "alice", "hunter2"

        result = screen.submit()

        self.assertTrue(result)
        self.assertEqual(screen.logged_in_username, "alice")
        self.assertFalse(screen.failed_last_attempt)
        self.assertEqual(screen.message, "Login successful")

    def test_failure_response_returns_false_and_sets_an_error_message(self):
        login_fn = Mock(return_value=LoginFailed("invalid_credentials"))
        screen = make_screen(login_fn)
        screen.username, screen.password = "alice", "wrong"

        result = screen.submit()

        self.assertFalse(result)
        self.assertIsNone(screen.logged_in_username)
        self.assertTrue(screen.failed_last_attempt)
        self.assertIn("invalid_credentials", screen.message)

    def test_enter_key_triggers_submit_and_reports_success(self):
        login_fn = Mock(return_value=LoginSucceeded("alice"))
        screen = make_screen(login_fn)
        screen.username, screen.password = "alice", "hunter2"

        self.assertTrue(screen.handle_key(ENTER_KEY))

    def test_enter_key_reports_failure(self):
        login_fn = Mock(return_value=LoginFailed("invalid_credentials"))
        screen = make_screen(login_fn)
        screen.username, screen.password = "alice", "wrong"

        self.assertFalse(screen.handle_key(ENTER_KEY))


if __name__ == "__main__":
    unittest.main()
