from CLIENT.config.constants import CELL_SIZE
from CLIENT.model.position import Position


class BoardMapper:

    def to_position(self, x, y):
        return Position(y // CELL_SIZE, x // CELL_SIZE)
