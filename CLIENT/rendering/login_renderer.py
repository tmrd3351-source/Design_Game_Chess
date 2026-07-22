from CLIENT.rendering import auth_theme as theme

NUM_FIELDS = 2
WIDTH = theme.WIDTH
HEIGHT = theme.total_height(NUM_FIELDS)

USERNAME_FIELD_RECT = theme.field_rect(0)
PASSWORD_FIELD_RECT = theme.field_rect(1)
SUBMIT_BUTTON_RECT = theme.submit_button_rect(NUM_FIELDS)
REGISTER_LINK_RECT = theme.link_button_rect(NUM_FIELDS)
CARD_HEIGHT = theme.card_height(NUM_FIELDS)
PANEL_Y = theme.panel_y(NUM_FIELDS)


class LoginRenderer:
    """Draws a LoginScreen's current state (username/password typed so far,
    which field is active, and any success/failure message) as a rounded
    card over a soft background, with a second panel below inviting the
    user to switch to RegisterScreen instead."""

    def render(self, login_screen):
        canvas = theme.background_canvas(HEIGHT)

        theme.draw_card(canvas, theme.CARD_X, theme.CARD_Y, theme.CARD_W, CARD_HEIGHT, theme.CARD_RADIUS)
        badge_cx = theme.CARD_X + theme.CARD_W // 2
        theme.draw_badge(canvas, badge_cx, theme.CARD_Y, theme.BADGE_RADIUS)
        theme.draw_lock_icon(canvas, badge_cx, theme.CARD_Y, scale=1.3)

        title = "Sign in to your account"
        title_x = theme.centered_text_x(title, theme.CARD_W, theme.CARD_X, font_size=0.65, thickness=2)
        canvas.put_text(title, title_x, theme.CARD_Y + 48, font_size=0.65, color=theme.TEXT_DARK, thickness=2)

        theme.draw_field(canvas, USERNAME_FIELD_RECT, login_screen.username,
                          "Username or email", login_screen.active_field == "username")
        theme.draw_field(canvas, PASSWORD_FIELD_RECT, login_screen.password,
                          "Password", login_screen.active_field == "password", masked=True)

        theme.draw_button(canvas, SUBMIT_BUTTON_RECT, "LOG IN")

        if login_screen.message:
            color = theme.ERROR_COLOR if login_screen.failed_last_attempt else theme.SUCCESS_COLOR
            msg_x = theme.centered_text_x(login_screen.message, theme.CARD_W, theme.CARD_X, font_size=0.5)
            msg_y = SUBMIT_BUTTON_RECT[1] + SUBMIT_BUTTON_RECT[3] + 26
            canvas.put_text(login_screen.message, msg_x, msg_y, font_size=0.5, color=color)

        theme.draw_card(canvas, theme.PANEL_X, PANEL_Y, theme.PANEL_W, theme.PANEL_H,
                         theme.PANEL_RADIUS, color=theme.PANEL_COLOR, border=theme.PANEL_COLOR)
        panel_badge_cx = theme.PANEL_X + theme.PANEL_W // 2
        theme.draw_badge(canvas, panel_badge_cx, PANEL_Y, theme.PANEL_BADGE_RADIUS)
        theme.draw_user_icon(canvas, panel_badge_cx, PANEL_Y, scale=1.1)

        prompt = "Don't have an account yet?"
        prompt_x = theme.centered_text_x(prompt, theme.PANEL_W, theme.PANEL_X, font_size=0.55, thickness=2)
        canvas.put_text(prompt, prompt_x, PANEL_Y + 46, font_size=0.55, color=theme.PANEL_TEXT, thickness=2)

        theme.draw_button(canvas, REGISTER_LINK_RECT, "REGISTER",
                           color=theme.CARD_COLOR, text_color=theme.TEXT_DARK)

        canvas.put_text("[Tab] switch field  [Enter] submit  [Esc] quit  (or click)",
                         theme.CARD_X, HEIGHT - 14, font_size=0.4, color=theme.PANEL_SUBTEXT)

        return canvas
