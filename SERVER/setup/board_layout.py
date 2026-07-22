import csv
from pathlib import Path

BOARD_CSV_PATH = Path(__file__).parent.parent.parent / "pictures" / "board.csv"


def load_layout(path=BOARD_CSV_PATH):
    """An 8x8 grid of piece codes (e.g. "RB"), '' for an empty square."""
    with open(path, newline="") as f:
        return [row for row in csv.reader(f) if row]
