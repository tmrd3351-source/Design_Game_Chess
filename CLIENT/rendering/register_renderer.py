from CLIENT.rendering import auth_theme as theme

NUM_FIELDS = 3
WIDTH = theme.WIDTH
HEIGHT = theme.total_height(NUM_FIELDS)

USERNAME_FIELD_RECT = theme.field_rect(0)
PASSWORD_FIELD_RECT = theme.field_rect(1)
CONFIRM_FIELD_RECT = theme.field_rect(2)
SUBMIT_BUTTON_RECT = theme.submit_button_rect(NUM_FIELDS)
LOGIN_LINK_RECT = theme.link_button_rect(NUM_FIELDS)
CARD_HEIGHT = theme.card_height(NUM_FIELDS)
PANEL_Y = theme.panel_y(NUM_FIELDS)


class RegisterRenderer:
    """Mirror image of LoginRenderer: a rounded card for the
    username/password/confirm-password form, with a panel below inviting the
    user back to LoginScreen instead."""

    def render(self, register_screen):
        canvas = theme.background_canvas(HEIGHT)

        theme.draw_card(canvas, theme.CARD_X, theme.CARD_Y, theme.CARD_W, CARD_HEIGHT, theme.CARD_RADIUS)
        badge_cx = theme.CARD_X + theme.CARD_W // 2
        theme.draw_badge(canvas, badge_cx, theme.CARD_Y, theme.BADGE_RADIUS)
        theme.draw_user_icon(canvas, badge_cx, theme.CARD_Y, scale=1.3)

        title = "Create a new account"
        title_x = theme.centered_text_x(title, theme.CARD_W, theme.CARD_X, font_size=0.65, thickness=2)
        canvas.put_text(title, title_x, theme.CARD_Y + 48, font_size=0.65, color=theme.TEXT_DARK, thickness=2)

        theme.draw_field(canvas, USERNAME_FIELD_RECT, register_screen.username,
                          "Choose a username", register_screen.active_field == "username")
        theme.draw_field(canvas, PASSWORD_FIELD_RECT, register_screen.password,
                          "Password", register_screen.active_field == "password", masked=True)
        theme.draw_field(canvas, CONFIRM_FIELD_RECT, register_screen.confirm_password,
                          "Confirm password", register_screen.active_field == "confirm_password", masked=True)

        theme.draw_button(canvas, SUBMIT_BUTTON_RECT, "REGISTER")

        if register_screen.message:
            color = theme.ERROR_COLOR if register_screen.failed_last_attempt else theme.SUCCESS_COLOR
            msg_x = theme.centered_text_x(register_screen.message, theme.CARD_W, theme.CARD_X, font_size=0.5)
            msg_y = SUBMIT_BUTTON_RECT[1] + SUBMIT_BUTTON_RECT[3] + 26
            canvas.put_text(register_screen.message, msg_x, msg_y, font_size=0.5, color=color)

        theme.draw_card(canvas, theme.PANEL_X, PANEL_Y, theme.PANEL_W, theme.PANEL_H,
                         theme.PANEL_RADIUS, color=theme.PANEL_COLOR, border=theme.PANEL_COLOR)
        panel_badge_cx = theme.PANEL_X + theme.PANEL_W // 2
        theme.draw_badge(canvas, panel_badge_cx, PANEL_Y, theme.PANEL_BADGE_RADIUS)
        theme.draw_lock_icon(canvas, panel_badge_cx, PANEL_Y, scale=1.1)

        prompt = "Already have an account?"
        prompt_x = theme.centered_text_x(prompt, theme.PANEL_W, theme.PANEL_X, font_size=0.55, thickness=2)
        canvas.put_text(prompt, prompt_x, PANEL_Y + 46, font_size=0.55, color=theme.PANEL_TEXT, thickness=2)

        theme.draw_button(canvas, LOGIN_LINK_RECT, "LOG IN",
                           color=theme.CARD_COLOR, text_color=theme.TEXT_DARK)

        canvas.put_text("[Tab] switch field  [Enter] submit  [Esc] quit  (or click)",
                         theme.CARD_X, HEIGHT - 14, font_size=0.4, color=theme.PANEL_SUBTEXT)

        return canvas
