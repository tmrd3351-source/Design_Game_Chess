from gui.canvas import Canvas

WIDTH = 500
HEIGHT = 260
BACKGROUND_COLOR = (40, 40, 40)

LABEL_COLOR = (255, 255, 255)
ACTIVE_FIELD_COLOR = (0, 220, 0)
INACTIVE_FIELD_COLOR = (200, 200, 200)
ERROR_COLOR = (0, 0, 255)
SUCCESS_COLOR = (0, 200, 0)


class LoginRenderer:
    """Draws a LoginScreen's current state (username/password typed so far,
    which field is active, and any success/failure message) onto a blank
    canvas - no board, no sprites, this isn't game rendering."""

    def render(self, login_screen):
        canvas = Canvas.blank(WIDTH, HEIGHT, BACKGROUND_COLOR)

        username_color = ACTIVE_FIELD_COLOR if login_screen.active_field == "username" else INACTIVE_FIELD_COLOR
        password_color = ACTIVE_FIELD_COLOR if login_screen.active_field == "password" else INACTIVE_FIELD_COLOR

        canvas.put_text("Username:", 30, 70, font_size=0.7, color=LABEL_COLOR)
        canvas.put_text(login_screen.username, 190, 70, font_size=0.7, color=username_color)

        canvas.put_text("Password:", 30, 120, font_size=0.7, color=LABEL_COLOR)
        canvas.put_text("*" * len(login_screen.password), 190, 120, font_size=0.7, color=password_color)

        if login_screen.message:
            message_color = ERROR_COLOR if login_screen.failed_last_attempt else SUCCESS_COLOR
            canvas.put_text(login_screen.message, 30, 180, font_size=0.6, color=message_color)

        canvas.put_text("[Tab] switch field  [Enter] submit  [Esc] quit",
                         20, HEIGHT - 20, font_size=0.45, color=LABEL_COLOR)

        return canvas
