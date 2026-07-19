import json
from pathlib import Path

from gui.canvas import Canvas
from config.constants import CELL_SIZE

PROJECT_ROOT = Path(__file__).parent.parent
ASSETS_DIR = Path(__file__).parent / "assets"
BOARD_IMAGE_PATH = ASSETS_DIR / "board.png"
PICTURES_DIR = PROJECT_ROOT / "pictures"

BOARD_SIDE = 8
BOARD_PIXELS = BOARD_SIDE * CELL_SIZE


def load_board_image() -> Canvas:
    return Canvas().read(BOARD_IMAGE_PATH, size=(BOARD_PIXELS, BOARD_PIXELS))


def load_piece_image(code: str, state: str = "idle", frame: int = 1) -> Canvas:
    path = PICTURES_DIR / code / "states" / state / "sprites" / f"{frame}.png"
    return Canvas().read(path, size=(CELL_SIZE, CELL_SIZE))


def _state_dir(code: str, state: str) -> Path:
    return PICTURES_DIR / code / "states" / state


def load_animation_config(code: str, state: str) -> dict:
    with open(_state_dir(code, state) / "config.json", encoding="utf-8") as f:
        return json.load(f)


def load_animation_frames(code: str, state: str) -> list[Canvas]:
    sprites_dir = _state_dir(code, state) / "sprites"
    frame_paths = sorted(sprites_dir.glob("*.png"), key=lambda p: int(p.stem))
    return [Canvas().read(path, size=(CELL_SIZE, CELL_SIZE)) for path in frame_paths]
