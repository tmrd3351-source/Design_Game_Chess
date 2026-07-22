from __future__ import annotations

import pathlib

import cv2
import numpy as np

class Canvas:
    def __init__(self):
        self.img = None

    @staticmethod
    def blank(width: int, height: int, color: tuple[int, int, int] = (30, 30, 30)) -> "Canvas":
        """A solid-color canvas not loaded from any file - for screens like
        the login form that don't have a background image."""
        canvas = Canvas()
        canvas.img = np.full((height, width, 3), color, dtype=np.uint8)
        return canvas

    @staticmethod
    def vertical_gradient(width: int, height: int, top_color: tuple[int, int, int],
                          bottom_color: tuple[int, int, int]) -> "Canvas":
        """A canvas whose background fades linearly from `top_color` at y=0
        to `bottom_color` at y=height - for screens with no background
        image of their own (login/register) that still want some depth."""
        top = np.array(top_color, dtype=np.float32).reshape(1, 1, 3)
        bottom = np.array(bottom_color, dtype=np.float32).reshape(1, 1, 3)
        t = np.linspace(0, 1, height, dtype=np.float32).reshape(height, 1, 1)
        row = top * (1 - t) + bottom * t
        canvas = Canvas()
        canvas.img = np.repeat(row, width, axis=1).astype(np.uint8)
        return canvas

    def read(self, path: str | pathlib.Path,
             size: tuple[int, int] | None = None,
             keep_aspect: bool = False,
             interpolation: int = cv2.INTER_AREA) -> "Canvas":
        """
        Load `path` into self.img and **optionally resize**.

        Parameters
        ----------
        path : str | Path
            Image file to load.
        size : (width, height) | None
            Target size in pixels.  If None, keep original.
        keep_aspect : bool
            • False  → resize exactly to `size`
            • True   → shrink so the *longer* side fits `size` while
                       preserving aspect ratio (no cropping).
        interpolation : OpenCV flag
            E.g.  `cv2.INTER_AREA` for shrink, `cv2.INTER_LINEAR` for enlarge.

        Returns
        -------
        Canvas
            `self`, so you can chain:  `sprite = Canvas().read("foo.png", (64,64))`
        """
        path = str(path)
        self.img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if self.img is None:
            raise FileNotFoundError(f"Cannot load image: {path}")

        if size is not None:
            target_w, target_h = size
            h, w = self.img.shape[:2]

            if keep_aspect:
                scale = min(target_w / w, target_h / h)
                new_w, new_h = int(w * scale), int(h * scale)
            else:
                new_w, new_h = target_w, target_h

            self.img = cv2.resize(self.img, (new_w, new_h), interpolation=interpolation)

        return self

    def draw_on(self, other_canvas, x, y):
        if self.img is None or other_canvas.img is None:
            raise ValueError("Both images must be loaded before drawing.")

        if self.img.shape[2] != other_canvas.img.shape[2]:
            if self.img.shape[2] == 3 and other_canvas.img.shape[2] == 4:
                self.img = cv2.cvtColor(self.img, cv2.COLOR_BGR2BGRA)
            elif self.img.shape[2] == 4 and other_canvas.img.shape[2] == 3:
                self.img = cv2.cvtColor(self.img, cv2.COLOR_BGRA2BGR)

        h, w = self.img.shape[:2]
        H, W = other_canvas.img.shape[:2]

        if y + h > H or x + w > W:
            raise ValueError("Logo does not fit at the specified position.")

        roi = other_canvas.img[y:y + h, x:x + w]

        if self.img.shape[2] == 4:
            b, g, r, a = cv2.split(self.img)
            mask = a / 255.0
            for c in range(3):
                roi[..., c] = (1 - mask) * roi[..., c] + mask * self.img[..., c]
        else:
            other_canvas.img[y:y + h, x:x + w] = self.img

    def extend_right(self, extra_width: int, color: tuple[int, int, int] = (30, 30, 30)) -> "Canvas":
        """A new Canvas: this image with `extra_width` pixels of solid
        `color` appended on the right (matching this image's channel
        count), for drawing a side panel next to the board."""
        height, _, channels = self.img.shape
        panel = np.zeros((height, extra_width, channels), dtype=self.img.dtype)
        panel[..., :3] = color
        if channels == 4:
            panel[..., 3] = 255
        combined = Canvas()
        combined.img = np.hstack([self.img, panel])
        return combined

    def blend_overlay(self, other_canvas, x, y, alpha):
        """Alpha-blends `other_canvas`'s image onto this one at (x, y) in
        place - for a faint decorative pattern (e.g. a checkerboard) behind
        a screen's real content. Unlike draw_on, this never treats the
        source as an opaque sprite to paste, always as a soft overlay, and
        silently clips instead of raising if it runs past either edge."""
        if self.img is None or other_canvas.img is None:
            return
        h, w = other_canvas.img.shape[:2]
        H, W = self.img.shape[:2]
        x1, y1 = max(x, 0), max(y, 0)
        x2, y2 = min(x + w, W), min(y + h, H)
        if x2 <= x1 or y2 <= y1:
            return
        roi = self.img[y1:y2, x1:x2]
        src = other_canvas.img[y1 - y:y2 - y, x1 - x:x2 - x, :3]
        for c in range(3):
            roi[..., c] = ((1 - alpha) * roi[..., c] + alpha * src[..., c]).astype(roi.dtype)

    def draw_overlay_rect(self, x, y, w, h, color, alpha):
        """Alpha-blend a solid BGR color rectangle onto this image in place.
        `color` is (B, G, R); `alpha` is 0 (invisible) .. 1 (opaque)."""
        if self.img is None or w <= 0 or h <= 0:
            return
        roi = self.img[y:y + h, x:x + w]
        for c in range(3):
            roi[..., c] = ((1 - alpha) * roi[..., c] + alpha * color[c]).astype(roi.dtype)

    def put_text(self, txt, x, y, font_size, color=(255, 255, 255, 255), thickness=1):
        if self.img is None:
            raise ValueError("Image not loaded.")
        cv2.putText(self.img, txt, (x, y),
                    cv2.FONT_HERSHEY_SIMPLEX, font_size,
                    color, thickness, cv2.LINE_AA)

    def draw_rounded_rect(self, x, y, w, h, radius, color, thickness=-1):
        """A rectangle with quarter-circle corners - the closest OpenCV
        primitives get to the rounded cards/inputs/buttons used by modern
        form UIs. `thickness=-1` fills it; any positive value draws only
        the outline (border)."""
        if self.img is None:
            raise ValueError("Image not loaded.")
        radius = min(radius, w // 2, h // 2)
        x2, y2 = x + w, y + h

        if thickness < 0:
            cv2.rectangle(self.img, (x + radius, y), (x2 - radius, y2), color, -1)
            cv2.rectangle(self.img, (x, y + radius), (x2, y2 - radius), color, -1)
        else:
            cv2.line(self.img, (x + radius, y), (x2 - radius, y), color, thickness, cv2.LINE_AA)
            cv2.line(self.img, (x + radius, y2), (x2 - radius, y2), color, thickness, cv2.LINE_AA)
            cv2.line(self.img, (x, y + radius), (x, y2 - radius), color, thickness, cv2.LINE_AA)
            cv2.line(self.img, (x2, y + radius), (x2, y2 - radius), color, thickness, cv2.LINE_AA)

        corners = [
            (x + radius, y + radius, 180),
            (x2 - radius, y + radius, 270),
            (x + radius, y2 - radius, 90),
            (x2 - radius, y2 - radius, 0),
        ]
        for cx, cy, start_angle in corners:
            cv2.ellipse(self.img, (cx, cy), (radius, radius), start_angle, 0, 90,
                        color, thickness, cv2.LINE_AA)

    def draw_circle(self, x, y, radius, color, thickness=-1):
        if self.img is None:
            raise ValueError("Image not loaded.")
        cv2.circle(self.img, (x, y), radius, color, thickness, cv2.LINE_AA)

    def draw_ellipse(self, x, y, axes, angle, start_angle, end_angle, color, thickness=-1):
        if self.img is None:
            raise ValueError("Image not loaded.")
        cv2.ellipse(self.img, (x, y), axes, angle, start_angle, end_angle, color, thickness, cv2.LINE_AA)

    def show(self):
        if self.img is None:
            raise ValueError("Image not loaded.")
        cv2.imshow("Image", self.img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
