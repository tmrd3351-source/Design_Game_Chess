from CLIENT.gui.canvas import Canvas

WIDTH = 500
HEIGHT = 260
BACKGROUND_COLOR = (40, 40, 40)

LABEL_COLOR = (255, 255, 255)
MESSAGE_COLOR = (0, 220, 220)
STARTED_COLOR = (0, 200, 0)
INPUT_COLOR = (0, 220, 0)


class HomeRenderer:
    """Draws a HomeScreen's current state: who's logged in, the available
    actions, and any status message (Waiting for an opponent.../Game
    started!) or the room ID being typed while joining. No board, no
    sprites - this isn't game rendering."""

    def render(self, home_screen):
        canvas = Canvas.blank(WIDTH, HEIGHT, BACKGROUND_COLOR)

        canvas.put_text(f"Logged in as {home_screen.username}", 30, 40, font_size=0.7, color=LABEL_COLOR)

        canvas.put_text("[P] Play", 30, 100, font_size=0.65, color=LABEL_COLOR)
        canvas.put_text("[C] Create Room", 30, 135, font_size=0.65, color=LABEL_COLOR)
        canvas.put_text("[J] Join Room", 30, 170, font_size=0.65, color=LABEL_COLOR)

        if home_screen.status == "entering_room_id":
            canvas.put_text(f"Room ID: {home_screen.room_id_input}_", 30, 215,
                             font_size=0.65, color=INPUT_COLOR)
        elif home_screen.message:
            message_color = STARTED_COLOR if home_screen.status == "started" else MESSAGE_COLOR
            canvas.put_text(home_screen.message, 30, 215, font_size=0.6, color=message_color)

        canvas.put_text("[Esc] quit", 20, HEIGHT - 20, font_size=0.45, color=LABEL_COLOR)

        return canvas
