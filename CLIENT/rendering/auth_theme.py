"""Shared visual language and layout geometry for LoginScreen and
RegisterScreen - two stacked rounded cards (the form itself, then a panel
inviting the user to the other screen) over a soft blue background, mirroring
each other closely enough that keeping their look in one module is what
actually keeps them looking like one product instead of two.

Card height depends on how many fields it holds (login has 2, register has
3), so geometry is computed from `num_fields` rather than hardcoded - the
panel below then simply starts wherever the card ends."""

import cv2

from CLIENT.gui.image import BOARD_IMAGE_PATH
from CLIENT.gui.canvas import Canvas

WIDTH = 520

# All colors are BGR (OpenCV convention), not RGB.
BG_TOP = (74, 58, 40)
BG_BOTTOM = (150, 118, 78)
BOARD_TINT_ALPHA = 0.10

CARD_COLOR = (255, 255, 255)
CARD_BORDER = (222, 217, 209)
CARD_SHADOW = (58, 46, 32)

PANEL_COLOR = (58, 35, 23)
PANEL_TEXT = (255, 255, 255)
PANEL_SUBTEXT = (196, 178, 158)

INPUT_BG = (241, 241, 241)
INPUT_BORDER_ACTIVE = (224, 111, 46)
INPUT_BORDER_INACTIVE = (208, 208, 208)
INPUT_TEXT = (60, 45, 30)
INPUT_PLACEHOLDER = (170, 160, 150)

TEXT_DARK = (74, 42, 27)
TEXT_MUTED = (150, 130, 110)

BUTTON_COLOR = (224, 111, 46)
BUTTON_TEXT = (255, 255, 255)

BADGE_COLOR = (224, 111, 46)
ICON_COLOR = (255, 255, 255)

ERROR_COLOR = (60, 60, 220)
SUCCESS_COLOR = (90, 175, 90)

# Card 1: the form itself (username/password[/confirm]).
CARD_X, CARD_Y, CARD_W = 60, 130, 400
CARD_RADIUS = 18
BADGE_RADIUS = 34

FIELD_X, FIELD_W, FIELD_H = CARD_X + 30, CARD_W - 60, 46
FIELD_GAP = 14
FIELD_TOP_OFFSET = 78  # CARD_Y -> first field's y
BUTTON_GAP = 14
MESSAGE_GAP = 26
CARD_BOTTOM_PADDING = 24

# Card 2: the "switch to the other screen" panel, sitting just below card 1.
PANEL_GAP = 32
PANEL_W, PANEL_H = 400, 140
PANEL_RADIUS = 18
PANEL_BADGE_RADIUS = 28
PANEL_X = CARD_X


def field_rect(index):
    y = CARD_Y + FIELD_TOP_OFFSET + index * (FIELD_H + FIELD_GAP)
    return FIELD_X, y, FIELD_W, FIELD_H


def submit_button_rect(num_fields):
    last_field_x, last_field_y, _, _ = field_rect(num_fields - 1)
    return FIELD_X, last_field_y + FIELD_H + BUTTON_GAP, FIELD_W, FIELD_H


def card_height(num_fields):
    _, button_y, _, button_h = submit_button_rect(num_fields)
    return (button_y + button_h) - CARD_Y + MESSAGE_GAP + CARD_BOTTOM_PADDING


def panel_y(num_fields):
    return CARD_Y + card_height(num_fields) + PANEL_GAP


def link_button_rect(num_fields):
    y = panel_y(num_fields)
    return PANEL_X + 40, y + 74, PANEL_W - 80, 44


def total_height(num_fields):
    return panel_y(num_fields) + PANEL_H + 40


def point_in_rect(px, py, rect):
    x, y, w, h = rect
    return x <= px <= x + w and y <= py <= y + h


def background_canvas(height):
    canvas = Canvas.vertical_gradient(WIDTH, height, BG_TOP, BG_BOTTOM)
    board = Canvas().read(BOARD_IMAGE_PATH, size=(WIDTH, height))
    canvas.blend_overlay(board, 0, 0, BOARD_TINT_ALPHA)
    return canvas


def draw_card_shadow(canvas, x, y, w, h, radius):
    canvas.draw_rounded_rect(x - 2, y + 6, w + 4, h + 4, radius, CARD_SHADOW)


def draw_card(canvas, x, y, w, h, radius, color=CARD_COLOR, border=CARD_BORDER):
    draw_card_shadow(canvas, x, y, w, h, radius)
    canvas.draw_rounded_rect(x, y, w, h, radius, color)
    canvas.draw_rounded_rect(x, y, w, h, radius, border, thickness=1)


def draw_badge(canvas, cx, cy, radius, color=BADGE_COLOR):
    canvas.draw_circle(cx, cy, radius, color)
    canvas.draw_circle(cx, cy, radius, CARD_COLOR, thickness=3)


def draw_user_icon(canvas, cx, cy, scale=1.0, color=ICON_COLOR):
    head_radius = int(6 * scale)
    canvas.draw_circle(cx, cy - int(4 * scale), head_radius, color)
    canvas.draw_ellipse(cx, cy + int(9 * scale), (int(10 * scale), int(8 * scale)), 0, 180, 360, color)


def draw_lock_icon(canvas, cx, cy, scale=1.0, color=ICON_COLOR):
    body_w, body_h = int(16 * scale), int(12 * scale)
    canvas.draw_rounded_rect(cx - body_w // 2, cy - int(1 * scale), body_w, body_h, radius=int(3 * scale), color=color)
    canvas.draw_ellipse(cx, cy - int(6 * scale), (int(7 * scale), int(7 * scale)), 0, 180, 360, color, thickness=max(2, int(2 * scale)))
    canvas.draw_circle(cx, cy + int(5 * scale), max(1, int(1.5 * scale)), CARD_COLOR)


def draw_field(canvas, rect, value, placeholder, active, masked=False):
    x, y, w, h = rect
    border = INPUT_BORDER_ACTIVE if active else INPUT_BORDER_INACTIVE
    canvas.draw_rounded_rect(x, y, w, h, 10, INPUT_BG)
    canvas.draw_rounded_rect(x, y, w, h, 10, border, thickness=2)

    text_x = x + 18
    text_y = y + h // 2 + 6
    shown = "•" * len(value) if masked else value
    if value:
        canvas.put_text(shown, text_x, text_y, font_size=0.55, color=INPUT_TEXT)
    else:
        canvas.put_text(placeholder, text_x, text_y, font_size=0.55, color=INPUT_PLACEHOLDER)

    if active:
        (text_w, _), _ = cv2.getTextSize(shown, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        cursor_x = text_x + text_w + 3
        canvas.draw_rounded_rect(cursor_x, y + 10, 2, h - 20, 0, INPUT_BORDER_ACTIVE)


def draw_button(canvas, rect, label, color=BUTTON_COLOR, text_color=BUTTON_TEXT):
    x, y, w, h = rect
    canvas.draw_rounded_rect(x, y, w, h, 10, color)
    (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
    text_x = x + (w - text_w) // 2
    text_y = y + (h + text_h) // 2
    canvas.put_text(label, text_x, text_y, font_size=0.6, color=text_color, thickness=2)


def centered_text_x(text, width, x_offset, font_size=0.6, thickness=1):
    """The x to pass to put_text so `text` ends up horizontally centered in
    a region of `width` starting at `x_offset`."""
    (text_w, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_size, thickness)
    return x_offset + (width - text_w) // 2
