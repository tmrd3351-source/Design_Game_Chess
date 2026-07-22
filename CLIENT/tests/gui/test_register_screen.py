import unittest
from unittest.mock import Mock

from CLIENT.gui.register_screen import RegisterScreen, TAB_KEY, BACKSPACE_KEY, ENTER_KEY, SWITCH_TO_LOGIN
from SHARED.network.protocol import RegisterSucceeded, RegisterFailed
from CLIENT.rendering.register_renderer import USERNAME_FIELD_RECT, PASSWORD_FIELD_RECT, CONFIRM_FIELD_RECT, \
    SUBMIT_BUTTON_RECT, LOGIN_LINK_RECT


def make_screen(register_fn=None):
    return RegisterScreen(server_uri="ws://unused", register_fn=register_fn or Mock())


def _center(rect):
    x, y, w, h = rect
    return x + w // 2, y + h // 2


def _type(screen, text):
    for char in text:
        screen.handle_key(ord(char))


class TestConstruction(unittest.TestCase):

    def test_starts_with_empty_fields_and_username_active(self):
        screen = make_screen()
        self.assertEqual(screen.username, "")
        self.assertEqual(screen.password, "")
        self.assertEqual(screen.confirm_password, "")
        self.assertEqual(screen.active_field, "username")
        self.assertEqual(screen.message, "")
        self.assertIsNone(screen.logged_in_username)


class TestTypingAndFieldSwitching(unittest.TestCase):

    def test_typed_characters_go_to_the_active_field(self):
        screen = make_screen()
        _type(screen, "alice")
        self.assertEqual(screen.username, "alice")
        self.assertEqual(screen.password, "")
        self.assertEqual(screen.confirm_password, "")

    def test_tab_cycles_through_all_three_fields(self):
        screen = make_screen()
        screen.handle_key(TAB_KEY)
        self.assertEqual(screen.active_field, "password")
        screen.handle_key(TAB_KEY)
        self.assertEqual(screen.active_field, "confirm_password")
        screen.handle_key(TAB_KEY)
        self.assertEqual(screen.active_field, "username")

    def test_backspace_removes_the_last_character_of_the_active_field(self):
        screen = make_screen()
        _type(screen, "alice")
        screen.handle_key(BACKSPACE_KEY)
        self.assertEqual(screen.username, "alic")


class TestSubmit(unittest.TestCase):

    def test_empty_username_is_rejected_without_calling_register_fn(self):
        register_fn = Mock()
        screen = make_screen(register_fn)
        screen.password = screen.confirm_password = "hunter2"

        result = screen.submit()

        self.assertFalse(result)
        register_fn.assert_not_called()
        self.assertTrue(screen.failed_last_attempt)

    def test_mismatched_passwords_are_rejected_without_calling_register_fn(self):
        register_fn = Mock()
        screen = make_screen(register_fn)
        screen.username = "alice"
        screen.password = "hunter2"
        screen.confirm_password = "hunter3"

        result = screen.submit()

        self.assertFalse(result)
        register_fn.assert_not_called()
        self.assertTrue(screen.failed_last_attempt)
        self.assertIn("match", screen.message)

    def test_calls_register_fn_with_the_typed_username_and_password(self):
        register_fn = Mock(return_value=RegisterSucceeded("alice"))
        screen = make_screen(register_fn)
        screen.username = "alice"
        screen.password = screen.confirm_password = "hunter2"

        screen.submit()

        register_fn.assert_called_once_with("alice", "hunter2")

    def test_success_response_returns_true_and_logs_the_user_in(self):
        register_fn = Mock(return_value=RegisterSucceeded("alice"))
        screen = make_screen(register_fn)
        screen.username = "alice"
        screen.password = screen.confirm_password = "hunter2"

        result = screen.submit()

        self.assertTrue(result)
        self.assertEqual(screen.logged_in_username, "alice")
        self.assertFalse(screen.failed_last_attempt)

    def test_failure_response_returns_false_and_sets_an_error_message(self):
        register_fn = Mock(return_value=RegisterFailed("username_taken"))
        screen = make_screen(register_fn)
        screen.username = "alice"
        screen.password = screen.confirm_password = "hunter2"

        result = screen.submit()

        self.assertFalse(result)
        self.assertIsNone(screen.logged_in_username)
        self.assertTrue(screen.failed_last_attempt)
        self.assertIn("username_taken", screen.message)

    def test_enter_key_triggers_submit_and_reports_success(self):
        register_fn = Mock(return_value=RegisterSucceeded("alice"))
        screen = make_screen(register_fn)
        screen.username = "alice"
        screen.password = screen.confirm_password = "hunter2"

        self.assertTrue(screen.handle_key(ENTER_KEY))


class TestHandleClick(unittest.TestCase):

    def test_clicking_the_confirm_field_makes_it_the_active_field(self):
        screen = make_screen()

        result = screen.handle_click(*_center(CONFIRM_FIELD_RECT))

        self.assertFalse(result)
        self.assertEqual(screen.active_field, "confirm_password")

    def test_clicking_the_username_field_makes_it_the_active_field(self):
        screen = make_screen()
        screen.active_field = "confirm_password"

        result = screen.handle_click(*_center(USERNAME_FIELD_RECT))

        self.assertFalse(result)
        self.assertEqual(screen.active_field, "username")

    def test_clicking_the_password_field_makes_it_the_active_field(self):
        screen = make_screen()

        result = screen.handle_click(*_center(PASSWORD_FIELD_RECT))

        self.assertFalse(result)
        self.assertEqual(screen.active_field, "password")

    def test_clicking_the_submit_button_submits_with_the_typed_credentials(self):
        register_fn = Mock(return_value=RegisterSucceeded("alice"))
        screen = make_screen(register_fn)
        screen.username = "alice"
        screen.password = screen.confirm_password = "hunter2"

        result = screen.handle_click(*_center(SUBMIT_BUTTON_RECT))

        self.assertTrue(result)
        register_fn.assert_called_once_with("alice", "hunter2")

    def test_clicking_the_login_link_requests_a_switch_and_stops_the_screen(self):
        screen = make_screen()

        result = screen.handle_click(*_center(LOGIN_LINK_RECT))

        self.assertTrue(result)
        self.assertTrue(screen.switch_to_login)

    def test_result_is_the_switch_to_login_sentinel_after_the_login_link(self):
        screen = make_screen()
        screen.handle_click(*_center(LOGIN_LINK_RECT))

        self.assertIs(screen._result(), SWITCH_TO_LOGIN)


if __name__ == "__main__":
    unittest.main()
